"""Signup, cookie-based JWT login/refresh/logout, and the current user's account endpoints.

The auth views set ``authentication_classes = []``: they never expect an access token, and
an expired one in the header must not block a login or a refresh.
"""

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenBackendError, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.state import token_backend
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.cookies import blacklist_all_for, clear_refresh_cookie, set_refresh_cookie
from accounts.models import RefreshRotation
from accounts.serializers import (
    AccessTokenSerializer,
    DeleteAccountSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    MeSerializer,
    PasswordChangeSerializer,
    SignupSerializer,
)

INVALID_CREDENTIALS = "Invalid username or password."
INVALID_REFRESH = "Refresh token is missing, invalid or revoked."


def response_with_new_tokens(user: User, body: dict) -> Response:
    refresh = RefreshToken.for_user(user)
    response = Response({"access": str(refresh.access_token), **body})
    set_refresh_cookie(response, str(refresh))
    return response


def unauthorized(detail: str) -> Response:
    return Response({"detail": detail}, status=status.HTTP_401_UNAUTHORIZED)


def refresh_rejected(refresh: str | None) -> Response:
    """
    Drop a dead refresh cookie along with the 401, unless it was only rotated away: then another
    tab refreshed first and the browser may already hold its successor, which must survive.
    """
    response = unauthorized(INVALID_REFRESH)
    if not is_rotated_away(refresh):
        clear_refresh_cookie(response)
    return response


def is_rotated_away(refresh: str | None) -> bool:
    jti = token_id(refresh) if refresh else None
    return jti is not None and BlacklistedToken.objects.filter(token__jti=jti).exists()


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    authentication_classes = []
    permission_classes = [AllowAny]


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses={200: LoginResponseSerializer})
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(request, **serializer.validated_data)
        if user is None:
            return unauthorized(INVALID_CREDENTIALS)
        return response_with_new_tokens(user, {"user": MeSerializer(user).data})


class RefreshView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={200: AccessTokenSerializer})
    def post(self, request: Request) -> Response:
        refresh = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if not refresh:
            return refresh_rejected(refresh)
        tokens = rotate(refresh) or rotate(recent_successor(refresh))
        if tokens is None:
            return refresh_rejected(refresh)
        response = Response({"access": tokens["access"]})
        set_refresh_cookie(response, tokens["refresh"])
        return response


def rotate(refresh: str | None) -> dict[str, str] | None:
    """Swap a valid refresh token for a new pair and remember the swap; None if the token is dead."""
    if refresh is None:
        return None
    serializer = TokenRefreshSerializer(data={"refresh": refresh})
    try:
        serializer.is_valid(raise_exception=True)
    except (TokenError, AuthenticationFailed):
        return None
    tokens = serializer.validated_data
    remember_rotation(refresh, tokens["refresh"])
    return tokens


def remember_rotation(old: str, new: str) -> None:
    """Record that ``new`` replaced ``old``, so a lost response can be recovered (see ``recent_successor``)."""
    predecessor = OutstandingToken.objects.filter(jti=token_id(old)).first()
    successor = OutstandingToken.objects.filter(jti=token_id(new)).first()
    if predecessor and successor:
        RefreshRotation.objects.update_or_create(predecessor=predecessor, defaults={"successor": successor})


def recent_successor(refresh: str) -> str | None:
    """
    The token that replaced this one, if the swap happened within the grace period. Logging out
    or changing the password blacklists the successor too, so rotating it then still fails.
    """
    try:
        claims = token_backend.decode(refresh, verify=True)
    except TokenBackendError:
        return None
    since = timezone.now() - settings.REFRESH_ROTATION_GRACE
    rotation = (
        RefreshRotation.objects.select_related("successor")
        .filter(predecessor__jti=claims.get("jti"), created_at__gte=since)
        .first()
    )
    return rotation.successor.token if rotation else None


def token_id(refresh: str) -> str | None:
    """The token's ``jti`` claim, read without checking expiry or the blacklist; None if unreadable."""
    try:
        return RefreshToken(refresh, verify=False)["jti"]
    except (TokenError, KeyError):
        return None


class LogoutView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={204: None})
    def post(self, request: Request) -> Response:
        refresh = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if refresh:
            revoke(refresh)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response


def revoke(refresh: str) -> None:
    try:
        RefreshToken(refresh).blacklist()
    except TokenError:
        # Already expired, revoked or malformed: there is nothing left to revoke.
        return


class MeView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_object(self) -> User:
        return self.request.user

    @extend_schema(request=DeleteAccountSerializer, responses={204: None})
    def delete(self, request: Request) -> Response:
        confirmation = DeleteAccountSerializer(data=request.data, context={"request": request})
        confirmation.is_valid(raise_exception=True)
        blacklist_all_for(request.user)
        request.user.delete()
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response


class PasswordChangeView(generics.GenericAPIView):
    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: AccessTokenSerializer})
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        blacklist_all_for(user)
        return response_with_new_tokens(user, {})

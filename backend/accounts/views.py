"""Signup, cookie-based JWT login/refresh/logout, and the current user's account endpoints.

The auth views set ``authentication_classes = []``: they never expect an access token, and
an expired one in the header must not block a login or a refresh.
"""

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.cookies import blacklist_all_for, clear_refresh_cookie, set_refresh_cookie
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
    response = Response({"detail": detail}, status=status.HTTP_401_UNAUTHORIZED)
    clear_refresh_cookie(response)
    return response


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
            return unauthorized(INVALID_REFRESH)
        serializer = TokenRefreshSerializer(data={"refresh": refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, AuthenticationFailed):
            return unauthorized(INVALID_REFRESH)
        response = Response({"access": serializer.validated_data["access"]})
        set_refresh_cookie(response, serializer.validated_data["refresh"])
        return response


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

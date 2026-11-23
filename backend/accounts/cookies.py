"""The refresh token lives only in an HttpOnly cookie; these helpers own that cookie."""

from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

SAME_SITE = "Strict"


def set_refresh_cookie(response: Response, refresh: str) -> None:
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        refresh,
        max_age=int(settings.REFRESH_TOKEN_LIFETIME.total_seconds()),
        path=settings.REFRESH_COOKIE_PATH,
        secure=settings.REFRESH_COOKIE_SECURE,
        httponly=True,
        samesite=SAME_SITE,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(settings.REFRESH_COOKIE_NAME, path=settings.REFRESH_COOKIE_PATH, samesite=SAME_SITE)


def blacklist_all_for(user: User) -> None:
    """Revoke every refresh token ever issued to the user, so no other session can refresh."""
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)

"""User profile kept next to Django's built-in User."""

from django.conf import settings
from django.db import models
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    favorite_club = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Profile of {self.user}"


class RefreshRotation(models.Model):
    """
    Which refresh token a rotation replaced with which. If the browser drops the response to a
    refresh (a reload while it is in flight), it still holds the old, now blacklisted token; for a
    short grace period the server accepts that token by rotating its successor instead.
    """

    predecessor = models.OneToOneField(OutstandingToken, on_delete=models.CASCADE, related_name="+")
    successor = models.ForeignKey(OutstandingToken, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.predecessor.jti} -> {self.successor.jti}"

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from accounts.models import Profile

WRONG_PASSWORD = "The password is incorrect."
USERNAME_TAKEN = User._meta.get_field("username").error_messages["unique"]


def ensure_username_free(username: str, owner: User | None = None) -> str:
    """
    Usernames are unique regardless of case: login is case-sensitive, so ``Luca`` and ``luca``
    would be two accounts that look like one player on the leaderboard.
    """
    others = User.objects.filter(username__iexact=username)
    if owner is not None:
        others = others.exclude(pk=owner.pk)
    if others.exists():
        raise serializers.ValidationError(USERNAME_TAKEN)
    return username


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["favorite_club", "country", "bio"]


def user_stats(user: User) -> dict[str, int]:
    attempts = list(user.attempts.all())
    total_correct = user.attempts.aggregate(total=Sum("score"))["total"] or 0
    best_score_pct = max((attempt.percent for attempt in attempts), default=0)
    return {"attempts": len(attempts), "total_correct": total_correct, "best_score_pct": best_score_pct}


class MeSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)
    stats = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "date_joined", "profile", "stats"]
        read_only_fields = ["id", "date_joined"]

    def get_stats(self, user: User) -> dict[str, int]:
        return user_stats(user)

    def validate_username(self, username: str) -> str:
        return ensure_username_free(username, owner=self.instance)

    @transaction.atomic
    def update(self, user: User, validated_data: dict) -> User:
        profile_data = validated_data.pop("profile", {})
        for field, value in validated_data.items():
            setattr(user, field, value)
        user.save()
        for field, value in profile_data.items():
            setattr(user.profile, field, value)
        user.profile.save()
        return user


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    favorite_club = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=100)
    country = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=100)

    class Meta:
        model = User
        fields = ["id", "username", "password", "favorite_club", "country"]
        read_only_fields = ["id"]

    def validate_username(self, username: str) -> str:
        return ensure_username_free(username)

    def validate(self, attrs: dict) -> dict:
        try:
            validate_password(attrs["password"], user=User(username=attrs["username"]))
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": list(error.messages)}) from error
        return attrs

    @transaction.atomic
    def create(self, validated_data: dict) -> User:
        profile_data = {
            field: validated_data.pop(field) for field in ("favorite_club", "country") if field in validated_data
        }
        user = User.objects.create_user(**validated_data)
        Profile.objects.filter(user=user).update(**profile_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"})


class AccessTokenSerializer(serializers.Serializer):
    access = serializers.CharField()


class LoginResponseSerializer(AccessTokenSerializer):
    user = MeSerializer()


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(style={"input_type": "password"})
    new_password = serializers.CharField(style={"input_type": "password"})

    def validate_old_password(self, old_password: str) -> str:
        if not self.context["request"].user.check_password(old_password):
            raise serializers.ValidationError(WRONG_PASSWORD)
        return old_password

    def validate_new_password(self, new_password: str) -> str:
        validate_password(new_password, user=self.context["request"].user)
        return new_password


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(style={"input_type": "password"})

    def validate_password(self, password: str) -> str:
        if not self.context["request"].user.check_password(password):
            raise serializers.ValidationError(WRONG_PASSWORD)
        return password

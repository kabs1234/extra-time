from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import Profile, RefreshRotation

PASSWORD = "kick-off-1863"
COOKIE = "refresh_token"


def end_rotation_grace() -> None:
    """Age every recorded rotation past the grace period, as if the browser had waited."""
    past = timezone.now() - settings.REFRESH_ROTATION_GRACE - timedelta(seconds=1)
    RefreshRotation.objects.update(created_at=past)


class SignupTests(APITestCase):
    def test_signup_creates_user_and_profile(self) -> None:
        response = self.client.post(
            "/api/auth/signup/",
            {"username": "newfan", "password": PASSWORD, "favorite_club": "Ajax"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="newfan")
        self.assertEqual(Profile.objects.get(user=user).favorite_club, "Ajax")

    def test_signup_rejects_username_that_differs_only_in_case(self) -> None:
        User.objects.create_user("newfan", password=PASSWORD)

        response = self.client.post("/api/auth/signup/", {"username": "NewFan", "password": PASSWORD}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["username"], ["A user with that username already exists."])

    def test_signup_rejects_weak_password(self) -> None:
        response = self.client.post("/api/auth/signup/", {"username": "newfan", "password": "123"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json())


class TokenFlowTests(APITestCase):
    def setUp(self) -> None:
        User.objects.create_user("player", password=PASSWORD)

    def login(self) -> str:
        response = self.client.post("/api/auth/login/", {"username": "player", "password": PASSWORD}, format="json")
        self.assertEqual(response.status_code, 200)
        return response.cookies[COOKIE].value

    def test_login_sets_httponly_refresh_cookie(self) -> None:
        response = self.client.post("/api/auth/login/", {"username": "player", "password": PASSWORD}, format="json")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("access", body)
        self.assertNotIn("refresh", body)
        self.assertEqual(body["user"]["username"], "player")
        cookie = response.cookies[COOKIE]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Strict")
        self.assertEqual(cookie["path"], "/api/auth/")

    def test_login_bad_credentials_is_401(self) -> None:
        response = self.client.post("/api/auth/login/", {"username": "player", "password": "wrong"}, format="json")

        self.assertEqual(response.status_code, 401)

    def test_failed_login_keeps_existing_session_cookie(self) -> None:
        self.login()

        response = self.client.post("/api/auth/login/", {"username": "player", "password": "wrong"}, format="json")

        self.assertEqual(response.status_code, 401)
        self.assertNotIn(COOKIE, response.cookies)
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 200)

    def test_refresh_with_cookie_returns_new_access_and_rotates(self) -> None:
        old_refresh = self.login()

        response = self.client.post("/api/auth/refresh/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertNotIn("refresh", response.json())
        self.assertNotEqual(response.cookies[COOKIE].value, old_refresh)
        end_rotation_grace()
        self.client.cookies[COOKIE] = old_refresh
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 401)

    def test_refresh_without_cookie_is_401(self) -> None:
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 401)

    def test_refresh_after_logout_is_401(self) -> None:
        refresh = self.login()

        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 204)

        self.client.cookies[COOKIE] = refresh
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 401)


class ParallelRefreshTests(APITestCase):
    def test_refresh_with_already_rotated_cookie_keeps_the_newer_cookie(self) -> None:
        User.objects.create_user("player", password=PASSWORD)
        old_refresh = self.client.post(
            "/api/auth/login/", {"username": "player", "password": PASSWORD}, format="json"
        ).cookies[COOKIE].value
        self.client.post("/api/auth/refresh/")
        end_rotation_grace()
        self.client.cookies[COOKIE] = old_refresh

        response = self.client.post("/api/auth/refresh/")

        self.assertEqual(response.status_code, 401)
        self.assertNotIn(COOKIE, response.cookies)


class RotationGraceTests(APITestCase):
    """A refresh whose response never reached the browser (a reload mid-request) must not end the session."""

    def setUp(self) -> None:
        self.user = User.objects.create_user("player", password=PASSWORD)
        response = self.client.post("/api/auth/login/", {"username": "player", "password": PASSWORD}, format="json")
        self.first_refresh = response.cookies[COOKIE].value
        self.access = response.json()["access"]
        self.lost_refresh = self.client.post("/api/auth/refresh/").cookies[COOKIE].value
        self.client.cookies[COOKIE] = self.first_refresh

    def test_replaying_a_just_rotated_cookie_rotates_its_successor(self) -> None:
        response = self.client.post("/api/auth/refresh/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        newest = response.cookies[COOKIE].value
        self.assertNotIn(newest, (self.first_refresh, self.lost_refresh))
        self.client.cookies[COOKIE] = newest
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 200)

    def test_the_lost_successor_is_revoked_once_replayed(self) -> None:
        self.client.post("/api/auth/refresh/")
        end_rotation_grace()

        self.client.cookies[COOKIE] = self.lost_refresh
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 401)

    def test_replay_after_logout_is_401(self) -> None:
        self.client.cookies[COOKIE] = self.lost_refresh
        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 204)

        self.client.cookies[COOKIE] = self.first_refresh
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 401)

    def test_replay_after_password_change_is_401(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")
        changed = self.client.post(
            "/api/me/password/", {"old_password": PASSWORD, "new_password": "brand-new-pass-99"}, format="json"
        )
        self.assertEqual(changed.status_code, 200)

        self.client.cookies[COOKIE] = self.first_refresh
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 401)

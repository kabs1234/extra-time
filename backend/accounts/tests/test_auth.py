from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from accounts.models import Profile

PASSWORD = "kick-off-1863"
COOKIE = "refresh_token"


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

    def test_refresh_with_cookie_returns_new_access_and_rotates(self) -> None:
        old_refresh = self.login()

        response = self.client.post("/api/auth/refresh/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertNotIn("refresh", response.json())
        self.assertNotEqual(response.cookies[COOKIE].value, old_refresh)
        self.client.cookies[COOKIE] = old_refresh
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 401)

    def test_refresh_without_cookie_is_401(self) -> None:
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 401)

    def test_refresh_after_logout_is_401(self) -> None:
        refresh = self.login()

        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 204)

        self.client.cookies[COOKIE] = refresh
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 401)

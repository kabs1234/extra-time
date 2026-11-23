from django.contrib.auth.models import User
from rest_framework.test import APITestCase

PASSWORD = "kick-off-1863"
COOKIE = "refresh_token"


class MeTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user("player", password=PASSWORD)
        User.objects.create_user("taken", password=PASSWORD)
        response = self.client.post("/api/auth/login/", {"username": "player", "password": PASSWORD}, format="json")
        self.refresh = response.cookies[COOKIE].value
        self.access = response.json()["access"]

    def authorize(self, access: str) -> None:
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_me_requires_auth(self) -> None:
        self.assertEqual(self.client.get("/api/me/").status_code, 401)

        self.authorize(self.access)
        response = self.client.get("/api/me/")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["username"], "player")
        self.assertIn("profile", body)
        self.assertEqual(body["stats"], {"attempts": 0, "total_correct": 0, "best_score_pct": 0})

    def test_change_username_and_profile(self) -> None:
        self.authorize(self.access)

        response = self.client.patch(
            "/api/me/", {"username": "renamed", "profile": {"country": "Brazil"}}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "renamed")
        self.assertEqual(response.json()["profile"]["country"], "Brazil")

    def test_change_username_conflict_is_400(self) -> None:
        self.authorize(self.access)

        response = self.client.patch("/api/me/", {"username": "taken"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.json())

    def test_password_change_wrong_old_is_400(self) -> None:
        self.authorize(self.access)

        response = self.client.post(
            "/api/me/password/", {"old_password": "wrong", "new_password": "brand-new-pass-99"}, format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("old_password", response.json())

    def test_password_change_rejects_weak_new_password(self) -> None:
        self.authorize(self.access)

        response = self.client.post(
            "/api/me/password/", {"old_password": PASSWORD, "new_password": "123"}, format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("new_password", response.json())

    def test_password_change_blacklists_old_refresh(self) -> None:
        self.authorize(self.access)

        response = self.client.post(
            "/api/me/password/", {"old_password": PASSWORD, "new_password": "brand-new-pass-99"}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        new_access = response.json()["access"]
        self.assertIn(COOKIE, response.cookies)
        self.client.cookies[COOKIE] = self.refresh
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 401)
        self.authorize(new_access)
        self.assertEqual(self.client.get("/api/me/").status_code, 200)

    def test_delete_account_requires_password(self) -> None:
        self.authorize(self.access)

        wrong = self.client.delete("/api/me/", {"password": "wrong"}, format="json")
        self.assertEqual(wrong.status_code, 400)
        self.assertIn("password", wrong.json())

        response = self.client.delete("/api/me/", {"password": PASSWORD}, format="json")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(username="player").exists())
        self.client.cookies[COOKIE] = self.refresh
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 401)

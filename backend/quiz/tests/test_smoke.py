from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.test import APITestCase


class ApiDocsTests(APITestCase):
    def test_api_docs_schema_is_public(self) -> None:
        response = self.client.get("/api/schema/")

        self.assertEqual(response.status_code, 200)


class AdminViewSiteTests(APITestCase):
    def test_view_site_link_opens_the_app_not_the_api_host(self) -> None:
        superuser = User.objects.create_superuser("root", password="kick-off-1863")
        self.client.force_login(superuser)

        response = self.client.get("/admin/")

        self.assertContains(response, f'href="{settings.FRONTEND_URL}"')

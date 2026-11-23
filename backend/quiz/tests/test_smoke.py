from rest_framework.test import APITestCase


class ApiDocsTests(APITestCase):
    def test_api_docs_schema_is_public(self) -> None:
        response = self.client.get("/api/schema/")

        self.assertEqual(response.status_code, 200)

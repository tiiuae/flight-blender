import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

JWT = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJ0ZXN0ZmxpZ2h0LmZsaWdodGJsZW5kZXIuY29tIiwiY2xpZW50X2lkIjoidXNzX25vYXV0aCIsImV4cCI6MTY4Nzc4Mjk0OCwiaXNzIjoiTm9BdXRoIiwianRpIjoiODI0OWI5ODgtZjlkZi00YmNhLWI2YTctODVhZGFiZjFhMTUwIiwibmJmIjoxNjg3Nzc5MzQ3LCJzY29wZSI6ImJsZW5kZXIucmVhZCIsInN1YiI6InVzc19ub2F1dGgifQ.b63qZWs08Cp1cgfRCtbQfLom6QQyFpqUaFDNZ9ZdAjSM690StACij6FiriSFhOfFiRBv9rE0DePJzElUSwv1r1bI0IpKMtEJYsJY4DXy7ZImiJ3rSten1nnb1LLAELcDIxMZM2D1ek43EFW35al4si640JfMcSmt62bEP1b4Msc"


class PublicKeyListTests(APITestCase):
    """
    Contains tests for the class PublicKeyList in views.
    """

    def setUp(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + JWT
        self.api_url = reverse("public_keys")

    def test_empty_json_payload(self):
        """
        The endpoint expects certain fields to be provided. Errors will be thrown otherwise.
        """
        empty_payload = {}
        response = self.client.post(
            self.api_url, content_type="application/json", data=empty_payload
        )
        response_json = {
            "key_id": ["This field is required."],
            "url": ["This field is required."],
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

    def test_invalid_json_payload(self):
        """
        The endpoint expects certain fields to be provided. Errors will be thrown otherwise.
        """
        invalid_payload = {"key_id": "1", "url": 12}
        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(invalid_payload),
        )
        response_json = {"url": ["Enter a valid URL."]}
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

    def test_invalid_json_payload_1(self):
        """
        The endpoint expects certain fields to be provided. Errors will be thrown otherwise.
        """
        invalid_payload = {"key_id": "", "url": ""}
        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(invalid_payload),
        )
        response_json = {
            "key_id": ["This field may not be blank."],
            "url": ["This field may not be blank."],
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

    def test_valid_payload(self):
        """
        Providing a valid payload
        """
        valid_payload = {"key_id": "001", "url": "https://publickeys.test.org"}
        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(valid_payload),
        )
        response_json = {
            "key_id": "001",
            "url": "https://publickeys.test.org",
            "is_active": True,
        }
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), response_json)

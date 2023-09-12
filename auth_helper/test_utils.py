import datetime
import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class RequiresScopesTests(APITestCase):
    def setUp(self):
        self.api_url = reverse("ping_auth")

    def test_valid_auth_token(self):
        valid_jwt = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJ0ZXN0ZmxpZ2h0LmZsaWdodGJsZW5kZXIuY29tIiwiY2xpZW50X2lkIjoidXNzX25vYXV0aCIsImV4cCI6MTY4Nzc4Mjk0OCwiaXNzIjoiTm9BdXRoIiwianRpIjoiODI0OWI5ODgtZjlkZi00YmNhLWI2YTctODVhZGFiZjFhMTUwIiwibmJmIjoxNjg3Nzc5MzQ3LCJzY29wZSI6ImJsZW5kZXIucmVhZCIsInN1YiI6InVzc19ub2F1dGgifQ.b63qZWs08Cp1cgfRCtbQfLom6QQyFpqUaFDNZ9ZdAjSM690StACij6FiriSFhOfFiRBv9rE0DePJzElUSwv1r1bI0IpKMtEJYsJY4DXy7ZImiJ3rSten1nnb1LLAELcDIxMZM2D1ek43EFW35al4si640JfMcSmt62bEP1b4Msc"
        self.client.defaults["HTTP_AUTHORIZATION"] = valid_jwt
        response = self.client.get(self.api_url, content_type="application/json")
        response_json = {"message": "pong with auth"}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), response_json)

    def test_no_auth_token(self):
        response = self.client.get(self.api_url, content_type="application/json")
        response_json = {"detail": "Authentication credentials were not provided"}
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), response_json)

    def test_malformed_auth_token(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = "one_worded_string"
        response = self.client.get(self.api_url, content_type="application/json")
        response_json = {"detail": "Authentication credentials are in incorrect form"}
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), response_json)


    def test_undecodable_auth_token(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer QAZWSXEDC"
        response = self.client.get(self.api_url, content_type="application/json")
        response_json = {"detail": "Bearer token could not be decoded properly"}
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), response_json)

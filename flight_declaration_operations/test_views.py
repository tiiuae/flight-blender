"""
This file contains unit tests for the views functions in flight_declaration_operations
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


JWT = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJ0ZXN0ZmxpZ2h0LmZsaWdodGJsZW5kZXIuY29tIiwiY2xpZW50X2lkIjoidXNzX25vYXV0aCIsImV4cCI6MTY4Nzc4Mjk0OCwiaXNzIjoiTm9BdXRoIiwianRpIjoiODI0OWI5ODgtZjlkZi00YmNhLWI2YTctODVhZGFiZjFhMTUwIiwibmJmIjoxNjg3Nzc5MzQ3LCJzY29wZSI6ImJsZW5kZXIucmVhZCIsInN1YiI6InVzc19ub2F1dGgifQ.b63qZWs08Cp1cgfRCtbQfLom6QQyFpqUaFDNZ9ZdAjSM690StACij6FiriSFhOfFiRBv9rE0DePJzElUSwv1r1bI0IpKMtEJYsJY4DXy7ZImiJ3rSten1nnb1LLAELcDIxMZM2D1ek43EFW35al4si640JfMcSmt62bEP1b4Msc"


class FlightDeclarationTests(APITestCase):
    """
    Contains tests for the function set_flight_declaration in views.
    """

    def setUp(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + JWT
        self.api_url =reverse("set_flight_declaration")
    
    def test_invalid_content_type(self):
        """
        The endpoint expects the content-type in application/json. If anything else is provided an error is thrown.
        """
        
        response = self.client.post(self.api_url, content_type="text/plain")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_invalid_payload(self):
        """
        The endpoint expects certain fields to be provided. Errors will be thrown otherwise.
        """
        invalid_payload = {}
        response = self.client.post(
            self.api_url, content_type="application/json", data=invalid_payload
        )
        response_json = {
            "originating_party": ["This field is required."],
            "start_datetime": ["This field is required."],
            "end_datetime": ["This field is required."],
            "type_of_operation": ["This field is required."],
            "flight_declaration_geo_json": ["This field is required."],
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

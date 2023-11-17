import uuid
from datetime import datetime

import pytest
from django.urls import reverse
from jwcrypto import jwk, jwt
from rest_framework import status
from rest_framework.test import APITestCase

from conftest import get_oauth2_token


class RequiresScopesTests(APITestCase):
    def setUp(self):
        self.api_url = reverse("ping_auth")
        self.dummy_private_key = jwk.JWK.from_pem(
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "MIICWwIBAAKBgHkNtpy3GB0YTCl2VCCd22i0rJwIGBSazD4QRKvH6rch0IP4igb+\n"
            "02r7t0X//tuj0VbwtJz3cEICP8OGSqrdTSCGj5Y03Oa2gPkx/0c0V8D0eSXS/CUC\n"
            "0qrYHnAGLqko7eW87HW0rh7nnl2bB4Lu+R8fOmQt5frCJ5eTkzwK5YczAgMBAAEC\n"
            "gYAtSgMjGKEt6XQ9IucQmN6Iiuf1LFYOB2gYZC+88PuQblc7uJWzTk08vlXwG3l3\n"
            "JQ/h7gY0n6JhH8RJW4m96TO8TrlHLx5aVcW8E//CtgayMn3vBgXida3wvIlAXT8G\n"
            "WezsNsWorXLVmz5yov0glu+TIk31iWB5DMs4xXhXdH/t8QJBALQzvF+y5bZEhZin\n"
            "qTXkiKqMsKsJbXjP1Sp/3t52VnYVfbxN3CCb7yDU9kg5QwNa3ungE3cXXNMUr067\n"
            "9zIraekCQQCr+NSeWAXIEutWewPIykYMQilVtiJH4oFfoEpxvecVv7ulw6kM+Jsb\n"
            "o6Pi7x86tMVkwOCzZzy/Uyo/gSHnEZq7AkEAm0hBuU2VuTzOyr8fhvtJ8X2O97QG\n"
            "C6c8j4Tk7lqXIuZeFRga6la091vMZmxBnPB/SpX28BbHvHUEpBpBZ5AVkQJAX7Lq\n"
            "7urg3MPafpeaNYSKkovG4NGoJgSgJgzXIJCjJfE6hTZqvrMh7bGUo9aZtFugdT74\n"
            "TB2pKncnTYuYyDN9vQJACDVr+wvYYA2VdnA9k+/1IyGc1HHd2npQqY9EduCeOGO8\n"
            "rXQedG6rirVOF6ypkefIayc3usipVvfadpqcS5ERhw==\n"
            "-----END RSA PRIVATE KEY-----".encode("UTF-8")
        )

    def test_valid_auth_token(self):
        token = get_oauth2_token()
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        response = self.client.get(self.api_url, content_type="application/json")
        response_json = {"message": "pong with auth"}
        self.assertEqual(response.json(), response_json)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

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

    def test_missing_iss_claim_auth_token(self):
        EPOCH = datetime.utcfromtimestamp(0)
        EXPIRATION_SECONDS = 1000
        timestamp = int((datetime.utcnow() - EPOCH).total_seconds())
        jwt_token = jwt.JWT(
            header={"typ": "JWT", "alg": "RS256"},
            claims={
                "sub": "uss_noauth",
                "client_id": "uss_noauth",
                "scope": " ".join("blender.read"),
                "aud": "alpha.flightblender.com",
                "nbf": timestamp - 1,
                "exp": timestamp + EXPIRATION_SECONDS,
                "jti": str(uuid.uuid4()),
            },
            algs=["RS256"],
        )
        jwt_token.make_signed_token(self.dummy_private_key)
        jwt_token = jwt_token.serialize()

        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + jwt_token
        response = self.client.get(self.api_url, content_type="application/json")
        response_json = {"detail": "Invalid token provided"}
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), response_json)

    @pytest.mark.usefixtures("mock_env_passport_url")
    def test_kid_claim_no_pub_key_server_auth_token(self):
        EPOCH = datetime.utcfromtimestamp(0)
        EXPIRATION_SECONDS = 1000
        timestamp = int((datetime.utcnow() - EPOCH).total_seconds())
        jwt_token = jwt.JWT(
            header={"typ": "JWT", "alg": "RS256", "kid": "qazwsx"},
            claims={
                "sub": "uss_noauth",
                "client_id": "uss_noauth",
                "scope": " ".join("blender.read"),
                "aud": "alpha.flightblender.com",
                "iss": "NoAuth",
                "nbf": timestamp - 1,
                "exp": timestamp + EXPIRATION_SECONDS,
                "jti": str(uuid.uuid4()),
            },
            algs=["RS256"],
        )
        jwt_token.make_signed_token(self.dummy_private_key)
        jwt_token = jwt_token.serialize()

        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + jwt_token

        response = self.client.get(self.api_url, content_type="application/json")
        response_json = {
            "detail": "Public Key Server to validate the token could not be reached"
        }
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), response_json)

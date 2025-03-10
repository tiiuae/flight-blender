import hashlib
import json
from datetime import datetime, timedelta
from unittest.mock import patch

import http_sfv
import pytest
import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)
from cryptography.x509.oid import NameOID
from django.test import TestCase
from http_message_signatures import (
    HTTPMessageSigner,
    HTTPMessageVerifier,
    HTTPSignatureKeyResolver,
    algorithms,
    structures,
)
from jwcrypto import jwk, jws

import security.helper as helper
from security.signing import MessageVerifier, ResponseSigner


class _TestCertificationCreator:
    def create_csr(self, pvt_key):
        csr = (
            x509.CertificateSigningRequestBuilder()
            .subject_name(
                x509.Name(
                    [
                        x509.NameAttribute(NameOID.COUNTRY_NAME, "FI"),
                        x509.NameAttribute(
                            NameOID.STATE_OR_PROVINCE_NAME, "TEST_Pirkanmaa"
                        ),
                        x509.NameAttribute(NameOID.LOCALITY_NAME, "TEST_Tampere"),
                        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "TEST_TII"),
                        x509.NameAttribute(NameOID.COMMON_NAME, "test.blender.api"),
                    ]
                )
            )
            .add_extension(
                x509.SubjectAlternativeName(
                    [
                        # Describe what sites we want this certificate for.
                        x509.DNSName("http://localhost:8000/"),
                    ]
                ),
                critical=False,
                # Sign the CSR with private key.
            )
            .sign(pvt_key, hashes.SHA256())
        )
        return csr

    def create_ca(self, pvt_key, csr):
        # Create a CA certificate
        ca_subject = x509.Name(
            [
                x509.NameAttribute(x509.NameOID.COUNTRY_NAME, "FI"),
                x509.NameAttribute(
                    x509.NameOID.STATE_OR_PROVINCE_NAME, "TEST_Pirkanmaa"
                ),
                x509.NameAttribute(x509.NameOID.LOCALITY_NAME, "TEST_Tampere"),
                x509.NameAttribute(x509.NameOID.ORGANIZATION_NAME, "TEST_TII"),
                x509.NameAttribute(x509.NameOID.COMMON_NAME, "test.blender.api"),
            ]
        )
        not_valid_before_time = datetime.utcnow()
        not_valid_after_time = not_valid_before_time + timedelta(days=365)
        ca_certificate = (
            x509.CertificateBuilder()
            .subject_name(ca_subject)
            .issuer_name(ca_subject)
            .public_key(pvt_key.public_key())
            .serial_number(x509.random_serial_number())
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=True
            )
            .not_valid_before(not_valid_before_time)
            .not_valid_after(not_valid_after_time)
            .sign(pvt_key, hashes.SHA256(), default_backend())
        )

        # Issue a certificate using the CSR and CA
        issued_certificate = (
            x509.CertificateBuilder()
            .subject_name(csr.subject)
            .issuer_name(ca_certificate.subject)
            .public_key(csr.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(not_valid_before_time)
            .not_valid_after(not_valid_after_time)
            .sign(pvt_key, hashes.SHA256(), default_backend())
        )
        return issued_certificate


class _TestHTTPSignatureKeyResolver(HTTPSignatureKeyResolver):
    def resolve_private_key(self, key_id: str):
        with open(f"security/test_keys/{key_id}.key", "rb") as fh:
            return load_pem_private_key(fh.read(), password=None)

    def resolve_public_key(self, key_id: str):
        with open(f"security/test_keys/{key_id}.pem", "rb") as fh:
            return load_pem_public_key(fh.read())


class _TestCertificationResolver:
    def __init__(self, pvt_key, cert_creator: _TestCertificationCreator):
        self._pvt_key = pvt_key
        self.cert_creator = cert_creator

    def resolve_public_key(self, key_id: str):
        csr = self.cert_creator.create_csr(pvt_key=self._pvt_key)
        ca = self.cert_creator.create_ca(pvt_key=self._pvt_key, csr=csr)
        return ca.public_key()


class MessageVerifierTests(TestCase):
    def setUp(self):
        # Create a request with payload
        self.key_id = "001"
        _payload = {"type_of_operation": 1, "originating_party": "TII"}
        _request = requests.Request(
            "POST",
            "http://localhost:8000/flight_declaration_ops/set_signed_flight_declaration",
            json=_payload,
        )

        _data = json.dumps(_payload, separators=(",", ":"))
        _content_digest = str(
            http_sfv.Dictionary({"sha-512": hashlib.sha512(_data.encode()).digest()})
        )

        # Sign the payload with RSA_PSS_SHA512 private key
        self.request = _request.prepare()
        self.request.headers["Content-Digest"] = _content_digest

        _signer = HTTPMessageSigner(
            signature_algorithm=algorithms.RSA_PSS_SHA512,
            key_resolver=_TestHTTPSignatureKeyResolver(),
        )
        _signer.sign(
            self.request,
            key_id=self.key_id,
            covered_component_ids=(
                "@method",
                "@authority",
                "@target-uri",
                "content-digest",
            ),
            label="sig1",
        )

    def test_check_signed_message_content(self):
        """
        Test whether the signed request has propper headers
        """
        assert self.request.headers.get("Content-Digest")
        assert self.request.headers.get("Signature-Input")
        assert self.request.headers.get("Signature")

    @patch("security.signing.MessageVerifier.get_public_keys")
    def test_verify_signed_message(self, mock_get_public_keys):
        """
        Test whether the signed request can be verified using the jwk of the public key
        """
        jwk = helper.get_jwk_from_public_pem_key(
            path=f"/app/security/test_keys/{self.key_id}.pem"
        )
        mock_get_public_keys.return_value = {self.key_id: jwk}

        django_request = helper.http_request_to_django_request(self.request)

        verifier = MessageVerifier()
        is_verified = verifier.verify_message(django_request)

        assert is_verified


class ResponseSigningTests(TestCase):
    def setUp(self):
        _payload = {"type_of_operation": 1, "originating_party": "TII"}
        _request = requests.Request(
            "POST",
            "http://localhost:8000/flight_declaration_ops/set_signed_flight_declaration",
            json=_payload,
        )
        self.request = _request.prepare()
        self.response_json = {
            "id": "0e036233-903b-49ab-8664-a35df14d7afa",
            "message": "Submitted Flight Declaration",
            "is_approved": False,
            "state": 1,
        }
        self.key_id = "001"

    def test_generate_content_digest(self):
        signer = ResponseSigner()
        actual = signer.generate_content_digest(payload=self.response_json)
        expected = "sha-512=:zplLMOJcNFs9REL0ZyRsobnKwMs7HtqbNTycHmS6nx33x2IcUjqJVxm7u9u1vH8Ry46uUxZ9jvyiXPqHun/IEQ==:"
        assert actual == expected

    @pytest.mark.usefixtures("mock_env_secret_key")
    def test_sign_json_via_jose(self):
        signer = ResponseSigner()
        signed_response = signer.sign_json_via_jose(payload=self.response_json)

        with open(f"security/test_keys/{self.key_id}.pem", "rb") as public_key_file:
            public_key_pem = public_key_file.read()

        public_key = jwk.JWK.from_pem(public_key_pem)
        # Verify the response json signed with JOSE by using the Public key
        token = signed_response["signature"]
        jws_token = jws.JWS()
        jws_token.deserialize(token)
        jws_token.verify(public_key)

        verified_payload_str = jws_token.payload.decode("utf-8")
        verified_payload_json = json.loads(verified_payload_str)
        assert verified_payload_json == self.response_json

    @pytest.mark.usefixtures("mock_env_secret_key")
    def test_sign_http_message_via_ietf(self):
        response_payload = {
            "id": "0e036233-903b-49ab-8664-a35df14d7afa",
            "message": "Submitted Flight Declaration",
            "is_approved": False,
            "state": 1,
        }
        signer = ResponseSigner()

        original_request = helper.http_request_to_django_request(self.request)
        signed_response = signer.sign_http_message_via_ietf(
            json_payload=response_payload, original_request=original_request
        )
        verifier = HTTPMessageVerifier(
            signature_algorithm=algorithms.RSA_PSS_SHA512,
            key_resolver=_TestHTTPSignatureKeyResolver(),
        )
        output = verifier.verify(signed_response)
        assert isinstance(output[0], structures.VerifyResult)


class CertTests(TestCase):
    def setUp(self):
        key_resolver = _TestHTTPSignatureKeyResolver()
        self.pvt_key = key_resolver.resolve_private_key(key_id="001")
        self.cert_creator = _TestCertificationCreator()

        _payload = {"type_of_operation": 1, "originating_party": "TII"}
        _request = requests.Request(
            "POST",
            "http://localhost:8000/flight_declaration_ops/set_signed_flight_declaration",
            json=_payload,
        )
        self.request = _request.prepare()

    def test_create_csr(self):
        csr = self.cert_creator.create_csr(pvt_key=self.pvt_key)
        self.assertIsInstance(csr, x509.CertificateSigningRequest)

    def test_create_ca(self):
        csr = self.cert_creator.create_csr(pvt_key=self.pvt_key)
        ca = self.cert_creator.create_ca(pvt_key=self.pvt_key, csr=csr)
        self.assertIsInstance(ca, x509.Certificate)
        public_key = ca.public_key()
        self.assertIsInstance(public_key, rsa.RSAPublicKey)

    @pytest.mark.usefixtures("mock_env_secret_key")
    def test_sign_and_verify(self):
        response_payload = {
            "id": "0e036233-903b-49ab-8664-a35df14d7afa",
            "message": "Submitted Flight Declaration",
            "is_approved": False,
            "state": 1,
        }
        signer = ResponseSigner()

        original_request = helper.http_request_to_django_request(self.request)
        signed_response = signer.sign_http_message_via_ietf(
            json_payload=response_payload, original_request=original_request
        )

        # Verify the signed request with CA's public key
        verifier = HTTPMessageVerifier(
            signature_algorithm=algorithms.RSA_PSS_SHA512,
            key_resolver=_TestCertificationResolver(
                pvt_key=self.pvt_key, cert_creator=self.cert_creator
            ),
        )
        output = verifier.verify(signed_response)
        assert isinstance(output[0], structures.VerifyResult)

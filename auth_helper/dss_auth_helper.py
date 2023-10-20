import json
import logging
from datetime import datetime, timedelta

import redis

from .common import get_redis

logger = logging.getLogger("django")
import json
from os import environ as env

import requests
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)


class AuthorityCredentialsGetter:
    """All calls to the DSS require credentials from a authority, usually the CAA since they can provide access to the system"""

    def __init__(self):
        pass

    def get_cached_credentials(self, audience: str, token_type: str):
        r = get_redis()

        now = datetime.now()
        token_suffix = "_auth_rid_token" if token_type == "rid" else "_auth_scd_token"
        cache_key = audience + token_suffix
        token_details = r.get(cache_key)

        if token_details:
            token_details = json.loads(token_details)
            created_at = token_details["created_at"]
            set_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%f")
            if now < (set_date - timedelta(minutes=58)):
                credentials = (
                    self.get_rid_credentials(audience=audience)
                    if token_type == "rid"
                    else self.get_scd_credentials(audience=audience)
                )

                r.set(
                    cache_key,
                    json.dumps(
                        {"credentials": credentials, "created_at": now.isoformat()}
                    ),
                )
            else:
                credentials = token_details["credentials"]
        else:
            credentials = (
                self.get_rid_credentials(audience=audience)
                if token_type == "rid"
                else self.get_scd_credentials(audience=audience)
            )

            access_token = credentials.get("access_token")
            if access_token:  # there is no error in the token
                r.set(
                    cache_key,
                    json.dumps(
                        {"credentials": credentials, "created_at": now.isoformat()}
                    ),
                )
                r.expire(cache_key, timedelta(minutes=58))

        return credentials

    def get_rid_credentials(self, audience: str):
        issuer = audience if audience == "localhost" else None

        if audience in ["localhost", "host.docker.internal"]:
            # Test instance of DSS
            payload = {
                "grant_type": "client_credentials",
                "intended_audience": env.get("DSS_SELF_AUDIENCE"),
                "scope": "dss.read.identification_service_areas dss.write.identification_service_areas",
                "issuer": issuer,
            }

        else:
            payload = {
                "grant_type": "client_credentials",
                "client_id": env.get("AUTH_DSS_CLIENT_ID"),
                "client_secret": env.get("AUTH_DSS_CLIENT_SECRET"),
                "audience": audience,
                "scope": "dss.read.identification_service_areas dss.write.identification_service_areas",
            }

        url = env.get("DSS_AUTH_URL") + env.get("DSS_AUTH_TOKEN_ENDPOINT")

        token_data = requests.get(url, params=payload)
        t_data = token_data.json()
        return t_data

    def get_scd_credentials(self, audience):
        issuer = audience if audience == "localhost" else None
        if audience in ["localhost", "host.docker.internal"]:
            # Test instance of DSS
            payload = {
                "grant_type": "client_credentials",
                "intended_audience": env.get("DSS_SELF_AUDIENCE"),
                "scope": "utm.strategic_coordination",
                "issuer": issuer,
            }

        else:
            payload = {
                "grant_type": "client_credentials",
                "client_id": env.get("AUTH_DSS_CLIENT_ID"),
                "client_secret": env.get("AUTH_DSS_CLIENT_SECRET"),
                "audience": audience,
                "scope": "utm.strategic_coordination",
            }

        url = env.get("DSS_AUTH_URL") + env.get("DSS_AUTH_TOKEN_ENDPOINT")

        token_data = requests.get(url, params=payload)
        t_data = token_data.json()

        return t_data

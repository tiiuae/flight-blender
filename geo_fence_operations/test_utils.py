from django.test import TestCase
from .utils import validate_geo_zone


class UtilTests(TestCase):
    def test_validate_geo_zone(self):
        empty_geo_zone_json = {}
        is_valid = validate_geo_zone(empty_geo_zone_json)
        self.assertEqual(is_valid, False)

        invalid_geo_zone_json = {
            "title": "Title is here",
            "description": " This is the description",
        }
        is_valid = validate_geo_zone(invalid_geo_zone_json)
        self.assertEqual(is_valid, False)

        valid_geo_zone_json_empty_features = {
            "title": "Title is here",
            "description": " This is the description",
            "features": [],
        }
        is_valid = validate_geo_zone(valid_geo_zone_json_empty_features)
        self.assertEqual(is_valid, True)

        valid_geo_zone_json = {
            "features": [
                {
                    "identifier": "string",
                    "country": "str",
                    "zoneAuthority": [
                        {
                            "name": "string",
                            "service": "string",
                            "contactName": "string",
                            "siteURL": "string",
                            "email": "string",
                            "phone": "string",
                            "purpose": "AUTHORIZATION",
                            "intervalBefore": "string",
                        }
                    ],
                    "name": "string",
                    "type": "COMMON",
                    "restriction": "string",
                    "restriction_conditions": ["string"],
                    "region": 65535,
                    "reason": ["AIR_TRAFFIC"],
                    "other_reason_info": "string",
                    "regulation_exemption": "YES",
                    "u_space_class": "string",
                    "message": "string",
                    "additional_properties": None,
                }
            ],
            "title": "Title is here",
            "description": " This is the description",
        }
        is_valid = validate_geo_zone(valid_geo_zone_json)
        self.assertEqual(is_valid, True)

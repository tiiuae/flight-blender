from django.test import TestCase
from .utils import validate_geo_zone
class UtilTests(TestCase):

    def test_validate_geo_zone(self):

        empty_geo_zone_json = {

        }
        is_valid = validate_geo_zone(empty_geo_zone_json)
        self.assertEqual(is_valid,False)

        invalid_geo_zone_json = {
            "title":"Tile is here",
            "description": " This is the description"
        }
        is_valid = validate_geo_zone(invalid_geo_zone_json)
        self.assertEqual(is_valid,False)

        valid_geo_zone_json = {
            "title":"Tile is here",
            "description": " This is the description",
            "features":[]
        }
        is_valid = validate_geo_zone(valid_geo_zone_json)
        self.assertEqual(is_valid,True)

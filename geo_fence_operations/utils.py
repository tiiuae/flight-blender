def validate_geo_zone(geo_zone) -> bool:
    """check whether the provided geozone is valid"""
    required_fields = {"title", "description", "features"}
    if all(k in geo_zone for k in required_fields):
        return True

    else:
        return False

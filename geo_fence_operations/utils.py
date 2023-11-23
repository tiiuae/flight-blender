import logging
from functools import partial
from typing import List, Tuple

import pyproj
import shapely.geometry as shp_geo
from shapely.geometry import Point, mapping
from shapely.ops import transform

from .data_definitions import (
    ED269Geometry,
    GeoZoneFeature,
    HorizontalProjection,
    ImplicitDict,
    ZoneAuthority,
)

logger = logging.getLogger("django")
proj_wgs84 = pyproj.Proj("+proj=longlat +datum=WGS84")


class GeoZoneParser:
    def __init__(self, geo_zone):
        self.geo_zone = geo_zone

    def parse_validate_geozone(
        self,
    ) -> (bool, Tuple[None, List[GeoZoneFeature]],):
        processed_geo_zone_features: List[GeoZoneFeature] = []
        all_zones_valid: List[bool] = []
        for _geo_zone_feature in self.geo_zone["features"]:
            zone_authorities = _geo_zone_feature["zoneAuthority"]
            all_zone_authorities = []
            for z_a in zone_authorities:
                zone_authority = ImplicitDict.parse(z_a, ZoneAuthority)
                all_zone_authorities.append(zone_authority)
            ed_269_geometries = []

            all_ed_269_geometries = _geo_zone_feature["geometry"]

            for ed_269_geometry in all_ed_269_geometries:
                parse_error = False
                if ed_269_geometry["horizontalProjection"]["type"] == "Polygon":
                    pass
                elif ed_269_geometry["horizontalProjection"]["type"] == "Circle":
                    try:
                        lat = ed_269_geometry["horizontalProjection"]["center"][1]
                        lng = ed_269_geometry["horizontalProjection"]["center"][0]
                        radius = ed_269_geometry["horizontalProjection"]["radius"]
                    except KeyError as ke:
                        logger.info(
                            "Error in parsing points provided in the ED 269 file %s"
                            % ke
                        )

                        parse_error = True
                    else:
                        r = radius / 1000  # Radius in km
                        buf = geodesic_point_buffer(lat, lng, r)
                        b = mapping(buf)
                        fc = {
                            "type": "FeatureCollection",
                            "features": [
                                {"type": "Feature", "properties": {}, "geometry": b}
                            ],
                        }
                        logger.info("Converting point to circle")
                        # logger.info(json.dumps(fc))
                        ed_269_geometry["horizontalProjection"] = b
                if not parse_error:
                    horizontal_projection = ImplicitDict.parse(
                        ed_269_geometry["horizontalProjection"], HorizontalProjection
                    )
                    parse_error = False
                    ed_269_geometry = ED269Geometry(
                        uomDimensions=ed_269_geometry["uomDimensions"],
                        lowerLimit=ed_269_geometry["lowerLimit"],
                        lowerVerticalReference=ed_269_geometry[
                            "lowerVerticalReference"
                        ],
                        upperLimit=ed_269_geometry["upperLimit"],
                        upperVerticalReference=ed_269_geometry[
                            "upperVerticalReference"
                        ],
                        horizontalProjection=horizontal_projection,
                    )
                    ed_269_geometries.append(ed_269_geometry)

            geo_zone_feature = GeoZoneFeature(
                identifier=_geo_zone_feature["identifier"],
                country=_geo_zone_feature["country"],
                name=_geo_zone_feature["name"],
                type=_geo_zone_feature["type"],
                restriction=_geo_zone_feature["restriction"],
                restrictionConditions=_geo_zone_feature["restrictionConditions"],
                region=_geo_zone_feature["region"],
                reason=_geo_zone_feature["reason"],
                otherReasonInfo=_geo_zone_feature["otherReasonInfo"],
                regulationExemption=_geo_zone_feature["regulationExemption"],
                uSpaceClass=_geo_zone_feature["uSpaceClass"],
                message=_geo_zone_feature["message"],
                applicability=_geo_zone_feature["applicability"],
                zoneAuthority=all_zone_authorities,
                geometry=ed_269_geometries,
            )
            processed_geo_zone_features.append(geo_zone_feature)
            all_zones_valid.append(True)

        return (
            all_zones_valid,
            processed_geo_zone_features,
        )


def validate_geo_zone(geo_zone) -> bool:
    """check whether the provided geozone is valid"""
    if all(k in geo_zone for k in ("title", "description", "features")):
        pass
    else:
        return False

    all_zones_valid = []
    geo_zone_parser = GeoZoneParser(geo_zone=geo_zone)
    all_zones_valid, _ = geo_zone_parser.parse_validate_geozone()

    if all(all_zones_valid):
        return True
    else:
        return False


def geodesic_point_buffer(lat, lon, km):
    # Azimuthal equidistant projection
    aeqd_proj = "+proj=aeqd +lat_0={lat} +lon_0={lon} +x_0=0 +y_0=0"
    project = partial(
        pyproj.transform, pyproj.Proj(aeqd_proj.format(lat=lat, lon=lon)), proj_wgs84
    )
    buf = Point(0, 0).buffer(km * 1000)  # distance in metres
    return transform(project, buf)


def toFromUTM(shp, proj, inv=False):
    """
    How to use?
    >>> import shapely.wkt
    >>> import shapely.geometry
    >>> proj = PROJECTION_IN # constant declared above the function definition
    >>> shp_obj = shapely.wkt.loads('LINESTRING(76.46019279956818 15.335048625850606,76.46207302808762 15.334717526558398)')
    >>> meters = 10
    >>> init_shape_utm = toFromUTM(shp_obj, proj)
    >>> buffer_shape_utm = init_shape_utm.buffer(meters)
    >>> buffer_shape_lonlat = toFromUTM(buffer_shape_utm, proj, inv=True)
    >>> out = shapely.geometry.mapping(buffer_shape_lonlat)
    >>> geojson = json.loads(json.dumps(out))

    Note: shp_obj is shapely object of type: Polygon, MultiPolygon, LineString and Point
    """
    geoInterface = shp.__geo_interface__

    shpType = geoInterface["type"]
    coords = geoInterface["coordinates"]

    if shpType == "Polygon":
        newCoord = [
            [proj(*point, inverse=inv) for point in linring] for linring in coords
        ]
    elif shpType == "MultiPolygon":
        newCoord = [
            [[proj(*point, inverse=inv) for point in linring] for linring in poly]
            for poly in coords
        ]
    elif shpType == "LineString":
        newCoord = [proj(*point, inverse=inv) for point in coords]
    elif shpType == "Point":
        newCoord = proj(*coords, inverse=inv)

    return shp_geo.shape({"type": shpType, "coordinates": tuple(newCoord)})

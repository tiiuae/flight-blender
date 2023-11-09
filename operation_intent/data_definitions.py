from dataclasses import dataclass
from typing import List, Literal, Optional


@dataclass
class LatLngPoint:
    """A class to hold information about a location as Latitude / Longitude pair"""

    lat: float
    lng: float


@dataclass
class Radius:
    """A class to hold the radius of a circle for the outline_circle object"""

    value: float
    units: str


@dataclass
class Polygon:
    """A class to hold the polygon object, used in the outline_polygon of the Volume3D object"""

    vertices: List[LatLngPoint]  # A minimum of three LatLngPoints are required


@dataclass
class Circle:
    """A class the details of a circle object used in the outline_circle object"""

    center: LatLngPoint
    radius: Radius


@dataclass
class Altitude:
    """A class to hold altitude information"""

    value: float
    reference: Literal["W84"]
    units: str


@dataclass
class Volume3D:
    """A class to hold Volume3D objects"""

    outline_circle: Optional[Circle]
    outline_polygon: Optional[Polygon]
    altitude_lower: Optional[Altitude]
    altitude_upper: Optional[Altitude]


@dataclass
class Time:
    """A class to hold Time details"""

    value: str
    format: Literal["RFC3339"]


@dataclass
class Volume4D:
    """A class to hold Volume4D objects"""

    volume: Volume3D
    time_start: Optional[Time]
    time_end: Optional[Time]


@dataclass
class FlightDeclarationOperationalIntentStorageDetails:
    volumes: List[Volume4D]
    off_nominal_volumes: List[Volume4D]
    priority: int
    state: str

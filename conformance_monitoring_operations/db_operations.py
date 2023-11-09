from typing import Tuple

from flight_declaration_operations import models as fdo_models


def get_flight_declaration_by_id(id: str) -> Tuple[None, fdo_models.FlightDeclaration]:
    try:
        flight_declaration = fdo_models.FlightDeclaration.objects.get(id=id)
        return flight_declaration
    except fdo_models.FlightDeclaration.DoesNotExist:
        return None


def get_flight_authorization_by_flight_declaration(
    flight_declaration: fdo_models.FlightDeclaration,
) -> Tuple[None, fdo_models.FlightAuthorization]:
    try:
        flight_authorization = fdo_models.FlightAuthorization.objects.get(
            declaration=flight_declaration
        )
        return flight_authorization
    except fdo_models.FlightDeclaration.DoesNotExist:
        return None
    except fdo_models.FlightAuthorization.DoesNotExist:
        return None

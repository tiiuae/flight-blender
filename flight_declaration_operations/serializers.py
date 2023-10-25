"""
This module holds the Serialization classes to be used in Flight Declaration operations.
"""
import json

from rest_framework import serializers

from common.data_definitions import OPERATION_STATES, OPERATOR_EVENT_LOOKUP
from conformance_monitoring_operations.conformance_checks_handler import (
    FlightOperationConformanceHelper,
)

from .models import FlightDeclaration
from .utils import OperationalIntentsConverter


class FlightDeclarationRequest:
    """
    Class object that will be used to contain deserialized JSON payload from the POST request.
    """

    def __init__(
        self,
        originating_party,
        start_datetime,
        end_datetime,
        type_of_operation,
        vehicle_id,
        submitted_by,
        flight_declaration_geo_json,
    ):
        self.originating_party = originating_party
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.type_of_operation = type_of_operation
        self.vehicle_id = vehicle_id
        self.submitted_by = submitted_by
        self.flight_declaration_geo_json = flight_declaration_geo_json


class FlightDeclarationRequestSerializer(serializers.Serializer):
    """
    Deserialize the JSON received payload for validation purposes.
    """

    originating_party = serializers.CharField(
        required=False, default="No Flight Information"
    )
    start_datetime = serializers.DateTimeField(required=False, default=None)
    end_datetime = serializers.DateTimeField(required=False, default=None)
    type_of_operation = serializers.IntegerField(required=False, default=0)
    vehicle_id = serializers.CharField(required=False, default="000")
    submitted_by = serializers.CharField(required=False, default=None)
    flight_declaration_geo_json = serializers.DictField(
        error_messages={
            "required": "A valid flight declaration as specified by the A flight declaration protocol must be submitted."
        }
    )

    def create(self, validated_data):
        return FlightDeclarationRequest(**validated_data)


class FlightDeclarationSerializer(serializers.ModelSerializer):
    """
    Serializer class for the model: FlightDeclaration
    """

    operational_intent = serializers.SerializerMethodField()
    flight_declaration_geojson = serializers.SerializerMethodField()
    flight_declaration_raw_geojson = serializers.SerializerMethodField()

    def get_flight_declaration_geojson(self, obj):
        o = obj.operational_intent

        my_operational_intent_converter = OperationalIntentsConverter()
        my_operational_intent_converter.convert_operational_intent_to_geo_json(
            volumes=o["volumes"]
        )

        return my_operational_intent_converter.geo_json

    def get_flight_declaration_raw_geojson(self, obj):
        return json.loads(obj.flight_declaration_raw_geojson)

    def get_operational_intent(self, obj):
        return obj.operational_intent

    class Meta:
        model = FlightDeclaration
        fields = (
            "operational_intent",
            "originating_party",
            "type_of_operation",
            "aircraft_id",
            "id",
            "state",
            "is_approved",
            "start_datetime",
            "end_datetime",
            "flight_declaration_geojson",
            "flight_declaration_raw_geojson",
            "approved_by",
            "submitted_by",
        )


class FlightDeclarationApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightDeclaration
        fields = (
            "is_approved",
            "approved_by",
        )


class FlightDeclarationStateSerializer(serializers.ModelSerializer):
    # Custom validator function to validate the state field when calling this class based model update view.
    def validate_state(self, value):
        if self.instance and value not in list(OPERATOR_EVENT_LOOKUP.keys()):
            raise serializers.ValidationError(
                "An operator can only set the state to Activated (2), Contingent (4) or Ended (5) using this endpoint"
            )

        current_state = self.instance.state

        if current_state == 5:
            raise serializers.ValidationError(
                "Cannot change state of an operation that has already set as ended"
            )

        event = OPERATOR_EVENT_LOOKUP[value]
        flight_declaration_id = str(self.instance.id)
        conformance_helper = FlightOperationConformanceHelper(
            flight_declaration_id=flight_declaration_id
        )
        transition_valid = conformance_helper.verify_operation_state_transition(
            original_state=current_state, new_state=value, event=event
        )

        if not transition_valid:
            raise serializers.ValidationError(
                "State transition to {new_state} from current state of {current_state} is not allowed per the ASTM standards".format(
                    new_state=OPERATION_STATES[value][1],
                    current_state=OPERATION_STATES[current_state][1],
                )
            )

        return value

    def update(self, instance, validated_data):
        fd = FlightDeclaration.objects.get(pk=instance.id)
        original_state = fd.state
        FlightDeclaration.objects.filter(pk=instance.id).update(**validated_data)

        # Save the database and trigger management command
        new_state = validated_data["state"]
        event = OPERATOR_EVENT_LOOKUP[new_state]
        fd.add_state_history_entry(
            original_state=original_state,
            new_state=new_state,
            notes="State changed by operator",
        )
        conformance_helper = FlightOperationConformanceHelper(
            flight_declaration_id=str(fd.id)
        )
        conformance_helper.manage_operation_state_transition(
            original_state=original_state, new_state=new_state, event=event
        )
        return fd

    class Meta:
        model = FlightDeclaration
        fields = (
            "state",
            "submitted_by",
        )

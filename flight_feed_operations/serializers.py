from rest_framework import serializers
import json
from .models import SignedTelmetryPublicKey

class SignedTelmetryPublicKeySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SignedTelmetryPublicKey        
        fields = ('key_id','url', 'is_active',)
   


class CurrentStateSerializer(serializers.Serializer):
    # Define fields for the "current_states" object if needed
    pass

class FlightDetailsSerializer(serializers.Serializer):
    # Define fields for the "flight_details" object if needed
    pass

class ObservationSerializer(serializers.Serializer):
    current_states = CurrentStateSerializer(many=True)
    flight_details = FlightDetailsSerializer()

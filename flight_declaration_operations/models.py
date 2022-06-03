from django.db import models
import uuid
from datetime import datetime
from django.utils.translation import gettext_lazy as _

class FlightOperation(models.Model):
    ''' A flight operation object for permission ''' 
    OPERATION_TYPES = ((0, _('VLOS')),(1, _('BVLOS')),)    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operational_intent = models.TextField()
    flight_declaration_geojson = models.TextField(null=True, blank=True)
    type_of_operation = models.IntegerField(choices=OPERATION_TYPES, default=0, help_text="At the moment, only VLOS and BVLOS operations are supported, for other types of operations, please issue a pull-request")
    bounds = models.CharField(max_length = 140)

    originating_party = models.CharField(max_length=100, help_text="Set the party originating this flight, you can add details e.g. Aerobridge Flight 105", default="Flight Blender Default")

    submitted_by = models.EmailField(blank= True, null= True)
    approved_by = models.EmailField(blank= True, null= True)

    start_datetime = models.DateTimeField(default=datetime.now)
    end_datetime = models.DateTimeField(default=datetime.now)
    is_approved = models.BooleanField(default =False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        
    def __unicode__(self):
       return self.name + ' ' + self.flight_plan.name

    def __str__(self):
        return self.name + ' ' + self.flight_plan.name
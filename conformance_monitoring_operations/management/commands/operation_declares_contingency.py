from django.core.management.base import BaseCommand, CommandError
from os import environ as env
from common.database_operations import BlenderDatabaseReader
from common.data_definitions import OPERATION_STATES
import arrow
from dotenv import load_dotenv, find_dotenv
import logging
from auth_helper.common import get_redis
import json
from scd_operations.dss_scd_helper import SCDOperations
from scd_operations.scd_data_definitions import Time, OperationalIntentReferenceDSSResponse, ImplicitSubscriptionParameters
from flight_feed_operations import flight_stream_helper
load_dotenv(find_dotenv())
 
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger('django')

class Command(BaseCommand):
    
    help = 'This command clears the operation in the DSS after the state has been set to ended.'

    def add_arguments(self, parser):

        parser.add_argument(
        "-o",
        "--flight_declaration_id",
        dest = "flight_declaration_id",
        metavar = "ID of the flight declaration",
        help='Specify the ID of Flight Declaration')

        parser.add_argument(
        "-d",
        "--dry_run",
        dest = "dry_run",
        metavar = "Set if this is a dry run",
        default= '1', 
        help='Set if it is a dry run')
        
        
    def handle(self, *args, **options):
        dry_run = options['dry_run']                 
        dry_run = 1 if dry_run =='1' else 0

        contingent_state = OPERATION_STATES[4][1]
        
        my_scd_dss_helper = SCDOperations()
        my_database_reader = BlenderDatabaseReader()
        now = arrow.now().isoformat()

        try:        
            flight_declaration_id = options['flight_declaration_id']
        except Exception as e:
            raise CommandError("Incomplete command, Flight Declaration ID not provided %s"% e)

        
        flight_declaration = my_database_reader.get_flight_declaration_by_id(flight_declaration_id= flight_declaration_id)
        if not flight_declaration: 
            raise CommandError("Flight Declaration with ID {flight_declaration_id} does not exist".format(flight_declaration_id = flight_declaration_id))
        flight_authorization = my_database_reader.get_flight_authorization_by_flight_declaration_obj(flight_declaration=flight_declaration)
        dss_operational_intent_ref_id = flight_authorization.dss_operational_intent_id
                
        r = get_redis()    
        
        flight_opint = 'flight_opint.'  + str(flight_declaration_id)   
        # Update the volume to create a new volume 
                
        if r.exists(flight_opint):
            op_int_details_raw = r.get(flight_opint)
            op_int_details = json.loads(op_int_details_raw)
            
            reference_full = op_int_details['success_response']['operational_intent_reference']
            dss_response_subscribers = op_int_details['success_response']['subscribers']
            details_full = op_int_details['operational_intent_details']
            # Load existing opint details

            stored_operational_intent_id= reference_full['id']
            stored_manager = reference_full['manager']
            stored_uss_availability = reference_full['uss_availability']
            stored_version = reference_full['version']
            stored_state = reference_full['state']
            stored_ovn = reference_full['ovn']
            stored_uss_base_url = reference_full['uss_base_url']
            stored_subscription_id = reference_full['subscription_id']
            
            stored_time_start = Time(format=reference_full['time_start']['format'], value=reference_full['time_start']['value'])
            stored_time_end = Time(format=reference_full['time_end']['format'], value=reference_full['time_end']['value'])

            stored_volumes = details_full['volumes']
            stored_priority = details_full['priority']
            stored_off_nominal_volumes = details_full['off_nominal_volumes']

            reference = OperationalIntentReferenceDSSResponse(id=stored_operational_intent_id, manager =stored_manager, uss_availability= stored_uss_availability, version= stored_version, state= stored_state, ovn = stored_ovn, time_start= stored_time_start, time_end = stored_time_end, uss_base_url=stored_uss_base_url, subscription_id=stored_subscription_id)
                
            if not dry_run:                 

                blender_base_url = env.get("BLENDER_FQDN", 0) 
                for subscriber in dss_response_subscribers:
                    subscriptions = subscriber['subscriptions']
                    uss_base_url = subscriber['uss_base_url']
                    if blender_base_url == uss_base_url:
                        for s in subscriptions:
                            subscription_id = s['subscription_id']
                            break
                # Create a new subscription to the airspace                
                operational_update_response = my_scd_dss_helper.update_specified_operational_intent_referecnce(subscription_id= subscription_id, operational_intent_ref_id = reference.id,extents= stored_volumes, new_state= str(contingent_state),ovn= reference.ovn, get_airspace_keys= False)


                ## Update / expnd volume
                        
                stream_ops = flight_stream_helper.StreamHelperOps()
                push_cg = stream_ops.push_cg()
                obs_helper = flight_stream_helper.ObservationReadOperations()
                all_flights_rid_data = obs_helper.get_observations(push_cg)
                # Get the last observation of the flight 
                # Update the volume

                ## Send the new volume to DSS

                # Notify others 





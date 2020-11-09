## This module polls 

import celery
import requests
import os, json
import logging
from os import environ as env
import redis
from datetime import timezone
from datetime import datetime, timedelta
from walrus import Database
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

REDIS_HOST = os.getenv('REDIS_HOST',"redis")
REDIS_PORT = 6379


class AuthorityCredentialsGetter():
    ''' All calls to the DSS require credentials from a authority, usually the CAA since they can provide access to the system '''
    def __init__(self):
        pass
        
    def get_cached_credentials(self, audience):  
        r = redis.Redis()
        
        now = datetime.now()
        cache_key = audience + '_auth_dss_token'
        token_details = r.get(cache_key)
        if token_details:    
            token_details = json.loads(token_details)
            created_at = token_details['created_at']
            set_date = datetime.strptime(created_at,"%Y-%m-%dT%H:%M:%S.%f")
            if now < (set_date - timedelta(minutes=58)):
                credentials = self.get_read_credentials(audience)
                r.set(cache_key, json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            else: 
                credentials = token_details['credentials']
        else:               
            credentials = self.get_read_credentials(audience)
            r.set(cache_key, json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))            
            r.expire(cache_key, timedelta(minutes=58))
            
        return credentials
            
        
    def get_read_credentials(self, audience):        
        payload = {"grant_type":"client_credentials","client_id": env.get('AUTH_DSS_CLIENT_ID'),"client_secret": env.get('AUTH_DSS_CLIENT_SECRET'),"audience":audience,"scope": 'dss.read_identification_service_areas'}        
        url = env.get('DSS_AUTH_URL') + env.get('DSS_AUTH_TOKEN_URL')        
        token_data = requests.post(url, data = payload)
        t_data = token_data.json()        
        return t_data



@celery.task()
def poll_uss_for_flights():


    my_credentials = AuthorityCredentialsGetter()
    credentials = my_credentials.get_read_credentials()
    
    flights_dict = redis.hgetall("all_uss_flights")

    all_flights_url = flights_dict['all_flights_url']
    flights_view = flights_dict['view']

    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + credentials}


    payload = {"view": flights_view}

    for cur_flight_url in all_flights_url:
        flights_response = requests.post(cur_flight_url, headers=headers)
        if flights_response.status_code == 200:
            # https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/uastech/standards/astm_rid_1.0/remoteid/canonical.yaml#tag/p2p_rid/paths/~1v1~1uss~1flights/get
            all_flights = flights_response['flights']
            for flight in all_flights:
                flight_id = flight['id']
                position = flight['current_state']['position']
                now  = datetime.now()
                time_stamp =  now.replace(tzinfo=timezone.utc).timestamp()
                
                payload = {"observations":[{"icao_address" : flight_id,"traffic_source" :1, "source_type" : 1, "lat_dd" : position['lat'], "lon_dd" : position['lng'], "time_stamp" : time_stamp,"altitude_mm" : position['alt']}]}

        else:
            logging.info(flights_response.status_code) 

    
    # Keep only the latest message
    distinct_messages = {i['address']:i for i in reversed(pending_messages)}.values()
    spotlight_host = os.getenv('SPOTLIGHT_HOST', 'http://localhost:5000')
    securl = spotlight_host + '/set_air_traffic'
    headers = {"Authorization": "Bearer " + credentials['access_token']}
    for message in distinct_messages:
        payload = {"icao_address" : message['icao_address'],"traffic_source" :message['traffic_source'], "source_type" : message['source_type'], "lat_dd" : message['lat_dd'], "lon_dd" : message['lon_dd'], "time_stamp" : message['time_stamp'],"altitude_mm" : message['altitude_mm']}
        response = requests.post(securl, data= payload, headers=headers)
        logging.info(response.status_code)



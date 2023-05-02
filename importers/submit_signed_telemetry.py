from http_message_signatures import HTTPMessageSigner, HTTPMessageVerifier, HTTPSignatureKeyResolver, algorithms
import requests, base64, hashlib, http_sfv

from auth_factory import NoAuthCredentialsGetter
import os
import json
from os.path import dirname, abspath
import  time
import arrow
import requests
from dataclasses import asdict
import rid_definitions
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)
# Source: https://github.com/pyauth/http-message-signatures/blob/main/test/test.py

test_shared_secret = base64.b64decode(
    "uzvJfB4u3N0Jy4T7NZ75MDVcr8zSTInedJtkgcu46YW4XByzNJjxBdtjUkdJPBtbmHhIDi6pcl8jsasj" "lTMtDQ=="
)

# class MyHTTPSignatureKeyResolver(HTTPSignatureKeyResolver):
#     keys = {"test-rsa-key": b"top-secret-key"}

#     def resolve_public_key(self, key_id: str):
#         return self.keys[key_id]

#     def resolve_private_key(self, key_id: str):
#         return self.keys[key_id]

class MyHTTPSignatureKeyResolver(HTTPSignatureKeyResolver):
    known_pem_keys = {"test-key-rsa-pss"}

    def resolve_public_key(self, key_id: str):

        if key_id in self.known_pem_keys:
            with open(f"keys/{key_id}.pem", "rb") as fh:
                return load_pem_public_key(fh.read())

    def resolve_private_key(self, key_id: str):
        if key_id in self.known_pem_keys:
            with open(f"keys/{key_id}.key", "rb") as fh: 
                return load_pem_private_key(fh.read(), password=None)

class BlenderUploader():
    
    def upload_to_server(self, filename):
        s = requests.Session()
        with open(filename, "r") as rid_json_file:
            rid_json = rid_json_file.read()
            
        rid_json = json.loads(rid_json)
        
        states = rid_json['current_states']
        rid_operator_details  = rid_json['flight_details']

        uas_id = rid_definitions.UASID(registration_id = 'CHE-5bisi9bpsiesw',  serial_number='d29dbf50-f411-4488-a6f1-cf2ae4d4237a',utm_id= '07a06bba-5092-48e4-8253-7a523f885bfe')
        eu_classification = rid_definitions.UAClassificationEU(category='Open', class_ = "Class0")
    
        rid_operator_details = rid_definitions.RIDOperatorDetails(
            id="382b3308-fa11-4629-a966-84bb96d3b4db",
            uas_id = uas_id,
            operation_description="Medicine Delivery",
            operator_id='CHE-076dh0dq',
            eu_classification = eu_classification,            
            operator_location=  rid_definitions.LatLngPoint(lat = 46.97615311620088,lng = 7.476099729537965)
        )

        for state in states: 
            now = arrow.now()
            headers = {"Content-Type":'application/json'}            
            # payload = {"observations":[{"icao_address" : icao_address,"traffic_source" :traffic_source, "source_type" : source_type, "lat_dd" : lat_dd, "lon_dd" : lon_dd, "time_stamp" : time_stamp,"altitude_mm" : altitude_mm, 'metadata':metadata}]}            

            payload = {"observations":[{"current_states":[state], "flight_details": {"rid_details" :asdict(rid_operator_details), "aircraft_type": "Helicopter","operator_name": "Thomas-Roberts" }}],}
                        
            try:
                            
                signed_r = requests.Request(method= 'PUT', url='http://localhost:8000/flight_stream/set_signed_telemetry', json=payload, headers= headers)
                signed_r = signed_r.prepare()
                signed_r.headers["Content-Digest"] = str(http_sfv.Dictionary({"sha-256": hashlib.sha256(signed_r.body).digest()}))
                
                signer = HTTPMessageSigner(signature_algorithm=algorithms.RSA_PSS_SHA512, key_resolver=MyHTTPSignatureKeyResolver())
                
                signer.sign(signed_r, created=now, label = "sig-b21", key_id="test-key-rsa-pss",covered_component_ids=(), nonce="b3k2pp5k7z-50gnwp.yemd", include_alg=False)
                
                response = s.send(signed_r)
                        
                
            except Exception as e:                
                print(e)
                break
            else:
                if response.status_code == 201:
                    print("Sleeping 3 seconds..")
                    time.sleep(3)
                else: 
                    print(response.json())


if __name__ == '__main__':
    
    parent_dir = dirname(abspath(__file__))  #<-- absolute dir the raw input file  is in
    
    rel_path = "rid_samples/flight_1_rid_aircraft_state.json"
    abs_file_path = os.path.join(parent_dir, rel_path)
    my_uploader = BlenderUploader()
    my_uploader.upload_to_server(filename=abs_file_path)
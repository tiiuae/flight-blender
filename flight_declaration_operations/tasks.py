from celery.utils.log import get_task_logger
import logging
from . import flight_declaration_rw_helper
from flight_blender.celery import app
from .models import FlightDeclaration
from pyle38 import Tile38
import asyncio

@app.task(name='write_flight_declaration_to_spotlight')
def write_flight_declaration_to_spotlight(fd):   
    my_credential_ops = flight_declaration_rw_helper.PassportCredentialsGetter()        
    fd_credentials = my_credential_ops.get_cached_credentials()
    
    try: 
        assert 'error' not in fd_credentials # Dictionary is populated 
    except AssertionError as e: 
        # Error in receiving a Flight Declaration credential
        logging.error('Error in getting Flight Declaration Token')
        logging.error(e)
    else:    
        my_uploader = flight_declaration_rw_helper.FlightDeclarationsUploader(credentials = fd_credentials)
        upload_status = my_uploader.upload_to_spotlight(flight_declaration_json=fd)

        logging.info(upload_status)

async def async_function(flight_declaration_id, flight_declaration_geo_json):
    # more async stuff...
    
    tile38 = Tile38(url="redis://localhost:9851", follower_url="redis://localhost:9851")
    await tile38.set(flight_declaration_id, "truck").point(52.25,13.37).exec()
    response = await tile38.within("fleet").circle(52.25, 13.37, 1000).asObjects()


@app.task(name="set_flight_declaration_geo_fence")
def set_flight_declaration_geo_fence(flight_declaration_id: str):
    '''
    This method creates a Geofence in Tile 38 backend. It takes the flight declaration ID and the GeoJSON and sets a GeoFence in Tile 38 against 
    '''
    fd_exists = FlightDeclaration.objects.filter(id = flight_declaration_id).exists()
    if fd_exists: 
        fd = FlightDeclaration.objects.get(id = flight_declaration_id)
        fd_geo_json = fd.flight_declaration_raw_geojson
        asyncio.run(async_function(flight_declaration_id, fd_geo_json))}}



    raise NotImplementedError
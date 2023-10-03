import logging
from os import environ as env

from dotenv import find_dotenv, load_dotenv

from flight_declaration_operations.tasks import send_operational_update_message

load_dotenv(find_dotenv())
logger = logging.getLogger("django")

class OperationConformanceNotification:
    def __init__(self, flight_declaration_id: str):
        self.flight_declaration_id = flight_declaration_id

    #TODO No need to have this function as it only calls send_operational_update_message()
    # Just implement the send_operational_update_message() logic here in Non conformance context. 
    # No need to import send_operational_update_message() from flight_declaration_operations
    def send_conformance_status_notification(self, message: str, level: str):    
        send_operational_update_message.delay(
            flight_declaration_id=self.flight_declaration_id,
            message_text=message,
            level=level,
        )


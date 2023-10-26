from dataclasses import dataclass
from enum import Enum


class NotificationLevel(Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


@dataclass
class NotificationMessage:
    """This object will hold messages that will go to the operational Notifications"""

    body: str
    level: str
    timestamp: str
    
    def to_dict(self):
        # Convert the obj to its string representation
        return {
            "body": self.body,
            "level": self.level,
            "timestamp": self.timestamp,
        }

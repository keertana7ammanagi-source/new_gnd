from enum import Enum
from dataclasses import dataclass
from typing import Optional

class CommandState(Enum):
    NOT_SENT = "Not Sent"
    SENT = "Sent"
    ACKNOWLEDGED = "Acknowledged"
    TIMEOUT = "Timeout"
    ERROR = "Error"

@dataclass
class Command:
    name: str
    description: str
    payload: Optional[str] = None  # None indicates explicitly unconfigured
    state: CommandState = CommandState.NOT_SENT
    require_confirmation: bool = False

# These are the required commands from the prompt.
# Wire payloads are NOT invented. They remain explicitly unconfigured (None) 
# until the CanSat firmware protocol is finalized.
COMMANDS = {
    "START_TELEMETRY": Command(
        name="START_TELEMETRY",
        description="Command the CanSat to start transmitting telemetry.",
        payload=None,
        require_confirmation=True
    ),
    "CALIBRATE_GYRO": Command(
        name="CALIBRATE_GYRO",
        description="Launch Pad: Calibrate Gyro",
        payload=None,
        require_confirmation=True
    ),
    "ZERO_BAROMETRIC_ALTITUDE": Command(
        name="ZERO_BAROMETRIC_ALTITUDE",
        description="Launch Pad: Zero Barometric Altitude",
        payload=None,
        require_confirmation=True
    ),
    "ZERO_ACCELEROMETER": Command(
        name="ZERO_ACCELEROMETER",
        description="Launch Pad: Zero Accelerometer",
        payload=None,
        require_confirmation=True
    )
}

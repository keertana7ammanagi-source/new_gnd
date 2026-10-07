from enum import Enum

class ExecutionMode(Enum):
    REAL = "REAL"
    SIMULATION = "SIMULATION"
    REPLAY = "REPLAY"

# Global Ground Station Settings

# Execution Mode
CURRENT_MODE = ExecutionMode.REAL

# Communication
SERIAL_PORT = "COM3"  # Change via UI or env if needed
BAUD_RATE = 115200
TIMEOUT = 1.0

# Telemetry
TEAM_ID = "2026-IN-SPACe-CAN-7USAT-XXX"

# Data Storage
DATA_DIR = "data"
CSV_PREFIX = "Flight"

# UI Settings
UI_REFRESH_RATE_HZ = 2.0
MAX_HISTORY_LENGTH = 5000  # Number of packets to keep in memory for plots

# Simulation
SIMULATION_RATE_HZ = 1.0

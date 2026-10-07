from dataclasses import dataclass
from typing import Any, Callable, Optional, Type

@dataclass
class TelemetryField:
    name: str
    index: int
    data_type: Type
    unit: str = ""
    precision: int = 2
    required: bool = True
    dashboard: bool = False
    plot: bool = False
    range_min: Optional[float] = None
    range_max: Optional[float] = None

SCHEMA_VERSION = "v1"
EXPECTED_FIELD_COUNT = 37

# Define the EXACT 37 fields
TELEMETRY_SCHEMA = [
    TelemetryField("TEAM_ID", 0, str, required=True),
    TelemetryField("TIMESTAMP", 1, float, unit="s", precision=3, dashboard=True, plot=True),
    TelemetryField("PACKET_COUNT", 2, int, dashboard=True, plot=True),
    TelemetryField("ALTITUDE", 3, float, unit="m", dashboard=True, plot=True),
    TelemetryField("PRESSURE", 4, float, unit="Pa", dashboard=True, plot=True),
    TelemetryField("TEMP", 5, float, unit="°C", dashboard=True, plot=True),
    TelemetryField("VOLTAGE", 6, float, unit="V", dashboard=True, plot=True),
    TelemetryField("GNSS_TIME", 7, float, unit="s"),
    TelemetryField("GNSS_LATITUDE", 8, float, unit="°", precision=6, dashboard=True),
    TelemetryField("GNSS_LONGITUDE", 9, float, unit="°", precision=6, dashboard=True),
    TelemetryField("GNSS_ALTITUDE", 10, float, unit="m", dashboard=True, plot=True),
    TelemetryField("GNSS_SATS", 11, int, dashboard=True, plot=True),
    TelemetryField("ACCEL_X", 12, float, unit="m/s²", plot=True),
    TelemetryField("ACCEL_Y", 13, float, unit="m/s²", plot=True),
    TelemetryField("ACCEL_Z", 14, float, unit="m/s²", plot=True),
    TelemetryField("GYRO_X", 15, float, unit="deg/s", plot=True),
    TelemetryField("GYRO_Y", 16, float, unit="deg/s", plot=True),
    TelemetryField("GYRO_Z", 17, float, unit="deg/s", plot=True),
    TelemetryField("MAG_X", 18, float, unit="uT", plot=True),
    TelemetryField("MAG_Y", 19, float, unit="uT", plot=True),
    TelemetryField("MAG_Z", 20, float, unit="uT", plot=True),
    TelemetryField("ROLL", 21, float, unit="°", dashboard=True, plot=True),
    TelemetryField("PITCH", 22, float, unit="°", dashboard=True, plot=True),
    TelemetryField("YAW", 23, float, unit="°", dashboard=True, plot=True),
    TelemetryField("LIGHT_LUX", 24, float, unit="lux", dashboard=True, plot=True),
    TelemetryField("UV_INDEX", 25, float, dashboard=True, plot=True),
    TelemetryField("HALL_RPM", 26, float, unit="RPM", dashboard=True, plot=True),
    TelemetryField("FLIGHT_SOFTWARE_STATE", 27, str, dashboard=True),
    TelemetryField("REL_ALTITUDE", 28, float, unit="m", dashboard=True, plot=True),
    TelemetryField("VERTICAL_SPEED", 29, float, unit="m/s", dashboard=True, plot=True),
    TelemetryField("GNSS_GROUND_SPEED", 30, float, unit="m/s", dashboard=True, plot=True),
    TelemetryField("GNSS_COURSE", 31, float, unit="°", dashboard=True, plot=True),
    TelemetryField("GNSS_HDOP", 32, float, dashboard=True, plot=True),
    TelemetryField("GNSS_FIX", 33, int, dashboard=True),
    TelemetryField("HUMIDITY", 34, float, unit="%RH", dashboard=True, plot=True),
    TelemetryField("CURRENT", 35, float, unit="A", dashboard=True, plot=True),
    TelemetryField("POWER", 36, float, unit="W", dashboard=True, plot=True),
]

# Create a fast lookup dict by index
SCHEMA_BY_INDEX = {field.index: field for field in TELEMETRY_SCHEMA}
SCHEMA_BY_NAME = {field.name: field for field in TELEMETRY_SCHEMA}

def validate_schema():
    """Validates the telemetry schema at module load time."""
    if len(TELEMETRY_SCHEMA) != EXPECTED_FIELD_COUNT:
        raise ValueError(f"CRITICAL: Schema field count is {len(TELEMETRY_SCHEMA)}, expected {EXPECTED_FIELD_COUNT}")
    
    seen_names = set()
    for i, field in enumerate(TELEMETRY_SCHEMA):
        if field.index != i:
            raise ValueError(f"CRITICAL: Schema field at array position {i} has incorrect index {field.index}. (Name: {field.name})")
        if field.name in seen_names:
            raise ValueError(f"CRITICAL: Duplicate field name found in schema: {field.name}")
        seen_names.add(field.name)

# Run validation immediately
validate_schema()

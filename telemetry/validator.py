from typing import Dict, Any, List, Tuple
from config.telemetry_schema import TELEMETRY_SCHEMA

# Known acceptable states for FLIGHT_SOFTWARE_STATE
VALID_FLIGHT_STATES = {
    "BOOT",
    "TEST_MODE",
    "LAUNCH_PAD",
    "ASCENT",
    "PRIMARY_DEPLOY",
    "DESCENT",
    "SECONDARY_DEPLOY",
    "IMPACT",
    "RECOVERY"
}

class TelemetryValidator:
    """
    Validates parsed telemetry data.
    Separates:
    - structural/schema errors (handled by parser)
    - suspicious/out-of-range values (handled here as warnings)
    """

    @staticmethod
    def validate(parsed_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validates the semantic content of a parsed packet.
        Does not reject packets based purely on range checks; issues warnings instead.
        
        Returns:
            (is_valid, warnings)
        """
        warnings = []
        is_valid = True

        for field in TELEMETRY_SCHEMA:
            val = parsed_data.get(field.name)
            
            # Required field check
            if field.required and val is None:
                warnings.append(f"Missing required field: {field.name}")
                is_valid = False # Missing required fields might make it invalid depending on strictness. Let's say yes.
                continue

            if val is None:
                continue

            # Range checks (configurable as warning)
            if field.data_type in (int, float):
                if field.range_min is not None and val < field.range_min:
                    warnings.append(f"{field.name} below range: {val} < {field.range_min}")
                if field.range_max is not None and val > field.range_max:
                    warnings.append(f"{field.name} above range: {val} > {field.range_max}")

        # Flight state specific check
        state = parsed_data.get("FLIGHT_SOFTWARE_STATE")
        if state and state not in VALID_FLIGHT_STATES:
            warnings.append(f"Unknown flight state: {state}")

        # Although we generated warnings, we don't invalidate the packet purely for ranges.
        # It's only invalid if required fields are utterly unparseable/missing.
        return is_valid, warnings

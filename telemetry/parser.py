from typing import Dict, Any, Tuple
from config.telemetry_schema import TELEMETRY_SCHEMA, EXPECTED_FIELD_COUNT

class SchemaMismatchError(Exception):
    """Raised when the packet does not match the exact expected field count."""
    pass

class TelemetryParser:
    @staticmethod
    def parse(raw_line: str) -> Tuple[Dict[str, Any], list[str]]:
        """
        Parses a raw CSV string into a dictionary based on the telemetry schema.
        
        Returns:
            (parsed_data, warnings)
            parsed_data: Dict mapping field names to parsed values.
            warnings: List of string warnings for things like type conversion issues 
                      that don't necessarily break the structure.
                      
        Raises:
            SchemaMismatchError if the field count is not exactly 37.
        """
        raw_line = raw_line.strip()
        if not raw_line:
            raise ValueError("Empty packet")

        parts = raw_line.split(',')
        
        if len(parts) != EXPECTED_FIELD_COUNT:
            raise SchemaMismatchError(f"Schema mismatch. Expected: {EXPECTED_FIELD_COUNT}, Received: {len(parts)}")

        parsed_data = {}
        warnings = []

        for i, field in enumerate(TELEMETRY_SCHEMA):
            raw_value = parts[i].strip()
            
            # Handle empty strings which might occur for optional sensors or dropped data
            if raw_value == "":
                parsed_data[field.name] = None
                if field.required:
                    warnings.append(f"Field {field.name} is required but was empty.")
                continue

            try:
                # Basic type conversion
                if field.data_type == int:
                    parsed_data[field.name] = int(raw_value)
                elif field.data_type == float:
                    parsed_data[field.name] = float(raw_value)
                elif field.data_type == str:
                    parsed_data[field.name] = str(raw_value)
                else:
                    parsed_data[field.name] = field.data_type(raw_value)
            except ValueError:
                parsed_data[field.name] = None
                warnings.append(f"Type conversion error for {field.name}. Expected {field.data_type.__name__}, got '{raw_value}'")

        return parsed_data, warnings

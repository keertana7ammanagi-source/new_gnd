import unittest
from telemetry.parser import TelemetryParser, SchemaMismatchError
from telemetry.validator import TelemetryValidator

# Valid 37-field mock data
VALID_PACKET = "2026-IN-SPACe-CAN-7USAT-XXX,100.0,1,10.0,101325.0,25.0,8.0,100.0,40.0,-75.0,10.0,6,0.0,0.0,9.8,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1000.0,1.0,0.0,ASCENT,10.0,5.0,10.0,180.0,1.0,1,50.0,1.0,8.0"
SHORT_PACKET = "2026-IN-SPACe-CAN-7USAT-XXX,100.0,1,10.0,101325.0,25.0,8.0,100.0,40.0,-75.0,10.0,6,0.0,0.0,9.8,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1000.0,1.0,0.0,ASCENT,10.0,5.0,10.0,180.0,1.0,1,50.0,1.0" # 36 fields
LONG_PACKET = VALID_PACKET + ",EXTRA_FIELD" # 38 fields

class TestParser(unittest.TestCase):
    def test_parse_valid_packet(self):
        data, warnings = TelemetryParser.parse(VALID_PACKET)
        self.assertEqual(len(data), 37)
        self.assertEqual(data["TEAM_ID"], "2026-IN-SPACe-CAN-7USAT-XXX")
        self.assertEqual(data["PACKET_COUNT"], 1)
        self.assertEqual(data["FLIGHT_SOFTWARE_STATE"], "ASCENT")
        self.assertEqual(len(warnings), 0)

    def test_parse_short_packet_raises_error(self):
        with self.assertRaises(SchemaMismatchError):
            TelemetryParser.parse(SHORT_PACKET)

    def test_parse_long_packet_raises_error(self):
        with self.assertRaises(SchemaMismatchError):
            TelemetryParser.parse(LONG_PACKET)

    def test_validator_warns_on_bad_state(self):
        data, _ = TelemetryParser.parse(VALID_PACKET)
        data["FLIGHT_SOFTWARE_STATE"] = "INVALID_STATE"
        is_valid, warnings = TelemetryValidator.validate(data)
        
        self.assertTrue(is_valid)  # Packets are not rejected for bad state, just warned
        self.assertTrue(any("Unknown flight state" in w for w in warnings))

if __name__ == '__main__':
    unittest.main()

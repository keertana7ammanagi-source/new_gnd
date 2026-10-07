import unittest
import os
import time
from unittest.mock import MagicMock
from telemetry.parser import TelemetryParser, SchemaMismatchError
from telemetry.validator import TelemetryValidator
from telemetry.packet_monitor import PacketMonitor
from telemetry.telemetry_manager import TelemetryManager
from storage.csv_logger import CSVLogger
from communication.command_sender import CommandSender
from config.commands import CommandState
from config.telemetry_schema import TELEMETRY_SCHEMA

# Valid 37-field mock data
VALID_PACKET = "2026-IN-SPACe-CAN-7USAT-XXX,100.0,1,10.0,101325.0,25.0,8.0,100.0,40.0,-75.0,10.0,6,0.0,0.0,9.8,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1000.0,1.0,0.0,ASCENT,10.0,5.0,10.0,180.0,1.0,1,50.0,1.0,8.0"
SHORT_PACKET = "2026-IN-SPACe-CAN-7USAT-XXX,100.0,1,10.0,101325.0,25.0,8.0,100.0,40.0,-75.0,10.0,6,0.0,0.0,9.8,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1000.0,1.0,0.0,ASCENT,10.0,5.0,10.0,180.0,1.0,1,50.0,1.0" # 36 fields
LONG_PACKET = VALID_PACKET + ",EXTRA_FIELD" # 38 fields
INVALID_NUMERIC = VALID_PACKET.replace(",101325.0,", ",BAD_PRESSURE,")
UNKNOWN_STATE = VALID_PACKET.replace(",ASCENT,", ",MAGIC_STATE,")
DUPLICATE_PACKET = VALID_PACKET
GAP_PACKET = "2026-IN-SPACe-CAN-7USAT-XXX,103.0,3,10.0,101325.0,25.0,8.0,100.0,40.0,-75.0,10.0,6,0.0,0.0,9.8,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1000.0,1.0,0.0,ASCENT,10.0,5.0,10.0,180.0,1.0,1,50.0,1.0,8.0"
BACKWARDS_PACKET = "2026-IN-SPACe-CAN-7USAT-XXX,99.0,0,10.0,101325.0,25.0,8.0,100.0,40.0,-75.0,10.0,6,0.0,0.0,9.8,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1000.0,1.0,0.0,ASCENT,10.0,5.0,10.0,180.0,1.0,1,50.0,1.0,8.0"

class TestBackendVerification(unittest.TestCase):

    def setUp(self):
        self.manager = TelemetryManager()
        self.monitor = self.manager.monitor

    def test_csv_header_correctness(self):
        logger = CSVLogger()
        self.assertTrue(os.path.exists(logger.filepath))
        with open(logger.filepath, 'r') as f:
            header_line = f.readline().strip()
        expected_header = ",".join([field.name for field in TELEMETRY_SCHEMA])
        self.assertEqual(header_line, expected_header)

    def test_valid_packet_reaches_csv_queue(self):
        logger = CSVLogger()
        parsed_data, w = TelemetryParser.parse(VALID_PACKET)
        logger.log_valid_packet(parsed_data)
        item_type, data = logger.queue.get_nowait()
        self.assertEqual(item_type, "VALID")
        self.assertEqual(data["TEAM_ID"], "2026-IN-SPACe-CAN-7USAT-XXX")

    def test_invalid_packet_does_not_reach_official_csv(self):
        logger = CSVLogger()
        logger.log_invalid_packet(SHORT_PACKET, "Schema Mismatch")
        item_type, data = logger.queue.get_nowait()
        self.assertEqual(item_type, "INVALID") # Not VALID

    def test_schema_mismatch_rejection(self):
        with self.assertRaises(SchemaMismatchError):
            TelemetryParser.parse(SHORT_PACKET)
        with self.assertRaises(SchemaMismatchError):
            TelemetryParser.parse(LONG_PACKET)

    def test_invalid_numeric_handling(self):
        data, warnings = TelemetryParser.parse(INVALID_NUMERIC)
        # Type conversion error warns, puts None
        self.assertIsNone(data["PRESSURE"])
        self.assertTrue(any("Type conversion error" in w for w in warnings))

    def test_unknown_flight_state_warning(self):
        data, parse_warns = TelemetryParser.parse(UNKNOWN_STATE)
        is_valid, val_warns = TelemetryValidator.validate(data)
        self.assertTrue(is_valid) # Not structurally rejected
        self.assertTrue(any("Unknown flight state" in w for w in val_warns))

    def test_packet_gap_detection(self):
        data1, _ = TelemetryParser.parse(VALID_PACKET) # count = 1
        data2, _ = TelemetryParser.parse(GAP_PACKET)   # count = 3
        self.monitor.process_packet(data1, True)
        self.monitor.process_packet(data2, True)
        self.assertEqual(self.monitor.total_lost, 1) # Missed count 2

    def test_duplicate_packet_handling(self):
        data1, _ = TelemetryParser.parse(VALID_PACKET)
        data2, _ = TelemetryParser.parse(DUPLICATE_PACKET)
        self.monitor.process_packet(data1, True)
        self.monitor.process_packet(data2, True)
        self.assertEqual(self.monitor.total_duplicates, 1)
        self.assertEqual(self.monitor.total_lost, 0)
        # Verify it wasn't silently discarded by checking it processed it
        self.assertEqual(self.monitor.total_received, 2)

    def test_packet_backwards_count(self):
        data1, _ = TelemetryParser.parse(VALID_PACKET) # count = 1
        data2, _ = TelemetryParser.parse(BACKWARDS_PACKET) # count = 0
        self.monitor.process_packet(data1, True)
        self.monitor.process_packet(data2, True)
        # Should not crash, should process normally without adding to lost
        self.assertEqual(self.monitor.total_lost, 0)

    def test_command_safety(self):
        # Create a mock receiver
        mock_receiver = MagicMock()
        mock_receiver.serial.is_open = True
        
        sender = CommandSender(self.manager, mock_receiver)
        
        # Try to send START_TELEMETRY which has NO configured payload
        result = sender.send_command("START_TELEMETRY")
        
        self.assertFalse(result)
        cmds = self.manager.get_commands()
        # Should be ERROR because payload is None
        self.assertEqual(cmds["START_TELEMETRY"].state, CommandState.ERROR)
        
        # State CANNOT become ACKNOWLEDGED automatically
        # Watchdog will only set it to TIMEOUT if it ever was SENT
        # Here it wasn't even sent.
        self.assertNotEqual(cmds["START_TELEMETRY"].state, CommandState.ACKNOWLEDGED)

if __name__ == '__main__':
    unittest.main()

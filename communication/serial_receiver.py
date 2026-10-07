import serial
import threading
import time
from typing import Optional
from telemetry.telemetry_manager import TelemetryManager
from storage.csv_logger import CSVLogger
from telemetry.parser import TelemetryParser, SchemaMismatchError
from telemetry.validator import TelemetryValidator

class SerialReceiver:
    def __init__(self, port: str, baud_rate: int, manager: TelemetryManager, logger: CSVLogger):
        self.port = port
        self.baud_rate = baud_rate
        self.manager = manager
        self.logger = logger
        
        self.serial: Optional[serial.Serial] = None
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

    def start(self):
        if self.thread is None or not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.serial and self.serial.is_open:
            self.serial.close()

    def _receive_loop(self):
        while not self.stop_event.is_set():
            if self.serial is None or not self.serial.is_open:
                self.manager.update_serial_status(False)
                try:
                    self.serial = serial.Serial(self.port, self.baud_rate, timeout=1.0)
                    self.manager.update_serial_status(True)
                except serial.SerialException:
                    time.sleep(2.0)  # Wait before retrying
                    continue

            try:
                raw_bytes = self.serial.readline()
                if not raw_bytes:
                    self.manager.update_serial_status(True) # Still open, just no data
                    continue
                
                raw_line = raw_bytes.decode('utf-8', errors='replace').strip()
                if not raw_line:
                    continue
                
                # Parse
                try:
                    parsed_data, parse_warnings = TelemetryParser.parse(raw_line)
                except SchemaMismatchError as e:
                    self.manager.add_invalid_raw(raw_line, str(e))
                    self.logger.log_invalid_packet(raw_line, str(e))
                    continue
                except Exception as e:
                    self.manager.add_invalid_raw(raw_line, f"Parse Error: {e}")
                    self.logger.log_invalid_packet(raw_line, f"Parse Error: {e}")
                    continue

                # Validate
                is_valid, val_warnings = TelemetryValidator.validate(parsed_data)
                warnings = parse_warnings + val_warnings

                # Update Manager
                self.manager.add_telemetry(raw_line, parsed_data, is_valid, warnings)
                
                # Update CSV (Only if valid)
                if is_valid:
                    self.logger.log_valid_packet(parsed_data)
                else:
                    self.logger.log_invalid_packet(raw_line, "Semantic validation failed")

            except serial.SerialException:
                self.serial.close()
                self.serial = None
            except Exception as e:
                print(f"Unexpected error in receiver loop: {e}")
                time.sleep(1.0)

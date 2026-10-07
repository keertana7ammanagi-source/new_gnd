import threading
import time
import math
from typing import Optional, Dict, Any
from config.settings import TEAM_ID
from telemetry.telemetry_manager import TelemetryManager
from storage.csv_logger import CSVLogger
from telemetry.parser import TelemetryParser, SchemaMismatchError
from telemetry.validator import TelemetryValidator

class TelemetrySimulator:
    def __init__(self, manager: TelemetryManager, logger: CSVLogger):
        self.manager = manager
        self.logger = logger
        
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Configuration
        self.rate_hz = 1.0
        self.deterministic = True
        
        # Fault injection config
        self.faults = {
            "packet_loss": False,
            "duplicate": False,
            "short_packet": False,
            "long_packet": False,
            "invalid_numeric": False,
            "missing_gnss": False,
            "delayed": False,
            "time_backwards": False,
            "count_backwards": False,
            "count_jump": False,
            "unknown_state": False,
            "out_of_range": False
        }
        
        self.reset()

    def reset(self):
        """Resets the simulation to the beginning."""
        self.packet_count = 0
        self.mission_time = 0.0
        self.state_index = 0
        self.states = [
            "BOOT", "TEST_MODE", "LAUNCH_PAD", "ASCENT", 
            "PRIMARY_DEPLOY", "DESCENT", "SECONDARY_DEPLOY", 
            "IMPACT", "RECOVERY"
        ]
        
        # Physics state
        self.altitude = 0.0
        self.vertical_speed = 0.0
        self.pressure = 101325.0
        self.temp = 25.0
        
        self.iteration = 0

    def start(self):
        if self.thread is None or not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2.0)

    def _simulation_loop(self):
        while not self.stop_event.is_set():
            start_t = time.time()
            
            # Step physics
            self._step_physics()
            
            # Generate Raw Line
            raw_line = self._generate_raw_csv()
            
            # Process exact same as SerialReceiver
            if self.faults["delayed"]:
                time.sleep(1.0) # Artificial delay
                
            self._process_raw_line(raw_line)
            
            if self.faults["duplicate"]:
                # Send the exact same line again
                self._process_raw_line(raw_line)
            
            # Sleep to match rate
            elapsed = time.time() - start_t
            sleep_time = max(0, (1.0 / self.rate_hz) - elapsed)
            time.sleep(sleep_time)

    def _process_raw_line(self, raw_line: str):
        try:
            parsed_data, parse_warnings = TelemetryParser.parse(raw_line)
        except SchemaMismatchError as e:
            self.manager.add_invalid_raw(raw_line, str(e))
            self.logger.log_invalid_packet(raw_line, str(e))
            return
        except Exception as e:
            self.manager.add_invalid_raw(raw_line, f"Parse Error: {e}")
            self.logger.log_invalid_packet(raw_line, f"Parse Error: {e}")
            return

        is_valid, val_warnings = TelemetryValidator.validate(parsed_data)
        warnings = parse_warnings + val_warnings

        self.manager.add_telemetry(raw_line, parsed_data, is_valid, warnings)
        
        if is_valid:
            self.logger.log_valid_packet(parsed_data)
        else:
            self.logger.log_invalid_packet(raw_line, "Semantic validation failed")

    def _step_physics(self):
        self.iteration += 1
        
        if not self.faults["time_backwards"]:
            self.mission_time += 1.0
        else:
            self.mission_time -= 1.0
            
        if self.faults["count_jump"]:
            self.packet_count += 5
        elif self.faults["count_backwards"]:
            self.packet_count -= 2
        elif self.faults["packet_loss"] and self.iteration % 10 == 0:
            self.packet_count += 2 # Simulate missed packet
        else:
            self.packet_count += 1
            
        # State transitions based on iteration
        if self.iteration >= 80:
            self.state_index = 8 # RECOVERY
        elif self.iteration >= 75:
            self.state_index = 7 # IMPACT
        elif self.iteration >= 60:
            self.state_index = 6 # SECONDARY_DEPLOY
        elif self.iteration >= 45:
            self.state_index = 5 # DESCENT
        elif self.iteration >= 40:
            self.state_index = 4 # PRIMARY_DEPLOY
        elif self.iteration >= 15:
            self.state_index = 3 # ASCENT
        elif self.iteration >= 10:
            self.state_index = 2 # LAUNCH_PAD
        elif self.iteration >= 5:
            self.state_index = 1 # TEST_MODE
        else:
            self.state_index = 0 # BOOT

        state = self.states[self.state_index]
        
        # Basic physics based on state
        if state == "ASCENT":
            self.vertical_speed = 20.0
            self.altitude += self.vertical_speed
            self.pressure -= 10.0
            self.temp -= 0.1
        elif state == "PRIMARY_DEPLOY":
            self.vertical_speed = -10.0
            self.altitude += self.vertical_speed
        elif state == "DESCENT":
            self.vertical_speed = -15.0
            self.altitude += self.vertical_speed
            self.pressure += 8.0
        elif state == "SECONDARY_DEPLOY":
            self.vertical_speed = -5.0
            self.altitude += self.vertical_speed
        elif state == "IMPACT" or state == "RECOVERY":
            self.vertical_speed = 0.0
            self.altitude = 0.0 # simplified
            self.pressure = 101325.0

    def _generate_raw_csv(self) -> str:
        state_str = self.states[self.state_index]
        if self.faults["unknown_state"]:
            state_str = "MAGIC_STATE"
            
        alt = self.altitude
        if self.faults["out_of_range"]:
            alt = 9999999.0
            
        gnss_fix = 1
        gnss_sats = 8
        if self.faults["missing_gnss"]:
            gnss_fix = 0
            gnss_sats = 0
            
        voltage = 8.4 - (self.iteration * 0.01)
        if self.faults["invalid_numeric"]:
            voltage_str = "BAD_VOLTAGE"
        else:
            voltage_str = f"{voltage:.2f}"
            
        # Exactly 37 fields
        # TEAM_ID,TIMESTAMP,PACKET_COUNT,ALTITUDE,PRESSURE,TEMP,VOLTAGE,GNSS_TIME,GNSS_LATITUDE,GNSS_LONGITUDE,GNSS_ALTITUDE,GNSS_SATS,ACCEL_X,ACCEL_Y,ACCEL_Z,GYRO_X,GYRO_Y,GYRO_Z,MAG_X,MAG_Y,MAG_Z,ROLL,PITCH,YAW,LIGHT_LUX,UV_INDEX,HALL_RPM,FLIGHT_SOFTWARE_STATE,REL_ALTITUDE,VERTICAL_SPEED,GNSS_GROUND_SPEED,GNSS_COURSE,GNSS_HDOP,GNSS_FIX,HUMIDITY,CURRENT,POWER
        fields = [
            TEAM_ID,
            str(int(self.mission_time)),
            str(self.packet_count),
            f"{alt:.1f}",
            f"{self.pressure:.1f}",
            f"{self.temp:.1f}",
            voltage_str,
            f"{self.mission_time + 100000:.1f}", # GNSS_TIME
            "40.000000",
            "-75.000000",
            f"{alt:.1f}",
            str(gnss_sats),
            "0.0", "0.0", "9.8", # ACCEL
            "0.0", "0.0", "0.0", # GYRO
            "30.0", "20.0", "10.0", # MAG
            "0.0", "0.0", "0.0", # RPY
            "1000.0", "1.0", "0.0", # LUX, UV, RPM
            state_str,
            f"{alt:.1f}", # REL_ALT
            f"{self.vertical_speed:.1f}",
            "0.0", "0.0", "1.0", str(gnss_fix), # GNSS Speed/Course/HDOP/FIX
            "50.0", "1.0", "8.0" # HUMIDITY, CURRENT, POWER
        ]
        
        if self.faults["short_packet"]:
            fields = fields[:-1] # 36 fields
        elif self.faults["long_packet"]:
            fields.append("EXTRA") # 38 fields
            
        return ",".join(fields)

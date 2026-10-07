import threading
import collections
from typing import Dict, Any, List, Optional
from telemetry.packet_monitor import PacketMonitor
from config.settings import MAX_HISTORY_LENGTH
from config.commands import COMMANDS, Command

class TelemetryManager:
    """
    Thread-safe central state repository for the ground station.
    The background threads write to this, and Streamlit reads from it.
    """
    def __init__(self):
        self._lock = threading.Lock()
        
        self.latest_telemetry: Optional[Dict[str, Any]] = None
        # Use a deque to efficiently bound memory usage for plots
        self.history = collections.deque(maxlen=MAX_HISTORY_LENGTH)
        
        self.monitor = PacketMonitor()
        self.commands: Dict[str, Command] = COMMANDS.copy()
        
        self.latest_raw_packet: str = ""
        self.warnings: List[str] = []

    def add_telemetry(self, raw_line: str, parsed_data: Dict[str, Any], is_valid: bool, warnings: List[str]):
        """Adds a new packet to the state in a thread-safe manner."""
        with self._lock:
            self.latest_raw_packet = raw_line
            self.monitor.process_packet(parsed_data, is_valid)
            
            if warnings:
                # Keep last 50 warnings
                self.warnings.extend(warnings)
                self.warnings = self.warnings[-50:]

            if is_valid:
                self.latest_telemetry = parsed_data
                self.history.append(parsed_data)

    def add_invalid_raw(self, raw_line: str, error_msg: str):
        """Records an invalid packet that failed schema parsing."""
        with self._lock:
            self.latest_raw_packet = raw_line
            self.monitor.process_invalid_packet()
            self.warnings.append(error_msg)
            self.warnings = self.warnings[-50:]

    def update_serial_status(self, is_open: bool):
        with self._lock:
            self.monitor.update_connection_status(is_open)

    # --- Read methods for Streamlit ---
    
    def get_latest(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.latest_telemetry.copy() if self.latest_telemetry else None

    def get_history(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.history)
            
    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_received": self.monitor.total_received,
                "total_lost": self.monitor.total_lost,
                "total_invalid": self.monitor.total_invalid,
                "total_duplicates": self.monitor.total_duplicates,
                "rate_hz": self.monitor.telemetry_rate_hz,
                "connection_text": self.monitor.connection_status.status_text,
                "is_connected": self.monitor.connection_status.is_connected
            }

    def get_latest_raw(self) -> str:
        with self._lock:
            return self.latest_raw_packet

    def get_commands(self) -> Dict[str, Command]:
        with self._lock:
            return self.commands.copy()
            
    def update_command_state(self, cmd_name: str, new_state):
        with self._lock:
            if cmd_name in self.commands:
                self.commands[cmd_name].state = new_state

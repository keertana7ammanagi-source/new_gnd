import time
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ConnectionStatus:
    is_connected: bool = False
    status_text: str = "SERIAL DISCONNECTED"
    last_packet_time: float = 0.0

class PacketMonitor:
    def __init__(self):
        self.total_received = 0
        self.total_lost = 0
        self.total_invalid = 0
        self.total_duplicates = 0
        
        self.last_packet_count: Optional[int] = None
        self.expected_next_count: Optional[int] = None
        
        self.telemetry_rate_hz = 0.0
        self.last_rate_calc_time = time.time()
        self.packets_since_calc = 0
        
        self.connection_status = ConnectionStatus()
        
    def process_packet(self, parsed_data: Dict[str, Any], is_valid: bool):
        """Called whenever a packet is processed by the parser/validator."""
        now = time.time()
        self.total_received += 1
        self.packets_since_calc += 1

        # Calculate rate every second
        if now - self.last_rate_calc_time >= 1.0:
            self.telemetry_rate_hz = self.packets_since_calc / (now - self.last_rate_calc_time)
            self.packets_since_calc = 0
            self.last_rate_calc_time = now

        if not is_valid:
            self.total_invalid += 1
            return

        self.connection_status.is_connected = True
        self.connection_status.status_text = "CONNECTED / RECEIVING"
        self.connection_status.last_packet_time = now

        current_count = parsed_data.get("PACKET_COUNT")
        if current_count is not None:
            if self.last_packet_count is not None:
                if current_count == self.last_packet_count:
                    self.total_duplicates += 1
                elif current_count < self.last_packet_count:
                    # Packet counter reset or out of order
                    pass # We just note it. Maybe CanSat restarted.
                else:
                    gap = current_count - self.expected_next_count
                    if gap > 0:
                        self.total_lost += gap

            self.last_packet_count = current_count
            self.expected_next_count = current_count + 1

    def process_invalid_packet(self):
        """Called for packets that fail basic schema matching (e.g., 36/38 fields)."""
        self.total_invalid += 1

    def update_connection_status(self, serial_open: bool):
        """Called periodically or when serial state changes to update high-level status."""
        now = time.time()
        if not serial_open:
            self.connection_status.is_connected = False
            self.connection_status.status_text = "SERIAL DISCONNECTED"
            self.telemetry_rate_hz = 0.0
            return

        time_since_last = now - self.connection_status.last_packet_time
        if time_since_last > 2.0: # Configurable timeout
            self.connection_status.is_connected = True
            self.connection_status.status_text = "CONNECTED / NO RECENT TELEMETRY"
            self.telemetry_rate_hz = 0.0

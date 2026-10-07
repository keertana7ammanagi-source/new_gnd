import os
import csv
import queue
import threading
from typing import Dict, Any, Optional
from config.settings import DATA_DIR, CSV_PREFIX, TEAM_ID, ExecutionMode
from config.telemetry_schema import TELEMETRY_SCHEMA

class CSVLogger:
    def __init__(self, mode: ExecutionMode = ExecutionMode.REAL):
        self.queue = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        prefix = CSV_PREFIX
        if mode == ExecutionMode.SIMULATION:
            prefix = f"Sim_{CSV_PREFIX}"
        elif mode == ExecutionMode.REPLAY:
            prefix = f"Replay_{CSV_PREFIX}"
            
        self.filepath = os.path.join(DATA_DIR, f"{prefix}_{TEAM_ID}.csv")
        self.error_filepath = os.path.join(DATA_DIR, f"{prefix}_{TEAM_ID}_errors.log")

        # Ensure directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Write headers if file doesn't exist
        file_exists = os.path.isfile(self.filepath)
        if not file_exists:
            with open(self.filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                headers = [field.name for field in TELEMETRY_SCHEMA]
                writer.writerow(headers)

    def start(self):
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.stop_event.clear()
            self.worker_thread = threading.Thread(target=self._logging_loop, daemon=True)
            self.worker_thread.start()

    def stop(self):
        self.stop_event.set()
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)

    def log_valid_packet(self, parsed_data: Dict[str, Any]):
        """Queues a valid packet to be written to the main CSV."""
        self.queue.put(("VALID", parsed_data))

    def log_invalid_packet(self, raw_line: str, error_msg: str):
        """Queues an invalid packet to be written to the error log."""
        self.queue.put(("INVALID", (raw_line, error_msg)))

    def _logging_loop(self):
        """Background thread that pops from the queue and writes to disk."""
        while not self.stop_event.is_set():
            try:
                # Block for up to 1 second waiting for data
                item_type, data = self.queue.get(timeout=1.0)
                
                if item_type == "VALID":
                    self._write_valid(data)
                elif item_type == "INVALID":
                    self._write_invalid(*data)
                    
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                # Basic error handling to keep thread alive
                print(f"CSV Writer error: {e}")

    def _write_valid(self, parsed_data: Dict[str, Any]):
        with open(self.filepath, 'a', newline='') as f:
            writer = csv.writer(f)
            # Ensure strict ordering from schema
            row = [parsed_data.get(field.name, "") for field in TELEMETRY_SCHEMA]
            writer.writerow(row)

    def _write_invalid(self, raw_line: str, error_msg: str):
        with open(self.error_filepath, 'a', encoding='utf-8') as f:
            f.write(f"ERROR: {error_msg} | RAW: {raw_line}\n")

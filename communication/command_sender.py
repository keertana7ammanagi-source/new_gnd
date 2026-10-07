import threading
import time
from typing import Optional
from telemetry.telemetry_manager import TelemetryManager
from config.commands import CommandState
from communication.serial_receiver import SerialReceiver

class CommandSender:
    def __init__(self, manager: TelemetryManager, receiver: SerialReceiver):
        self.manager = manager
        self.receiver = receiver

    def send_command(self, cmd_name: str) -> bool:
        """
        Sends a command through the active serial connection.
        Updates the command state in the TelemetryManager.
        """
        commands = self.manager.get_commands()
        if cmd_name not in commands:
            return False

        cmd = commands[cmd_name]
        
        if cmd.payload is None:
            # Explicitly unconfigured. Refuse to send.
            self.manager.update_command_state(cmd_name, CommandState.ERROR)
            print(f"Command {cmd_name} is explicitly unconfigured (no payload).")
            return False

        if not self.receiver.serial or not self.receiver.serial.is_open:
            self.manager.update_command_state(cmd_name, CommandState.ERROR)
            return False

        try:
            self.receiver.serial.write(cmd.payload.encode('utf-8'))
            self.manager.update_command_state(cmd_name, CommandState.SENT)
            
            # Start a watchdog thread to handle timeouts if ACK doesn't come
            # We NO LONGER simulate ACK. It goes to TIMEOUT unless the CanSat firmware responds.
            threading.Thread(target=self._watchdog, args=(cmd_name,), daemon=True).start()
            return True
        except Exception as e:
            print(f"Command send error: {e}")
            self.manager.update_command_state(cmd_name, CommandState.ERROR)
            return False

    def _watchdog(self, cmd_name: str):
        """Simple watchdog to mark a command as timeout if no ACK is received."""
        # Wait for timeout period
        time.sleep(3.0)
        cmds = self.manager.get_commands()
        # If state is still SENT, it means we never received an ACK.
        # It must NEVER become ACKNOWLEDGED without a valid ACK being parsed from telemetry.
        if cmds.get(cmd_name).state == CommandState.SENT:
            self.manager.update_command_state(cmd_name, CommandState.TIMEOUT)

# flightLogic/command_listener.py
import asyncio
import struct
import sys # For sys.exit

from . import command_defs
from . import shared_state # Use this if shared_state.py is created

# If not using shared_state.py, these would be global here or passed in:
# telemetry_enabled = True
# telemetry_interval_seconds = 10.0
# app_restart_requested = False


COMMAND_LISTEN_IP = "0.0.0.0" # Listen on all available interfaces
COMMAND_LISTEN_PORT = 9090

class CommandProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport
        print(f"Command UDP server listening on {COMMAND_LISTEN_IP}:{COMMAND_LISTEN_PORT}")

    def datagram_received(self, data, addr):
        print(f"Received command from {addr}: {data.hex()}")
        try:
            cmd_id, payload = command_defs.unpack_command_id(data)

            if cmd_id == command_defs.CMD_ID_ENABLE_TELEMETRY:
                print("CMD: Enable Telemetry")
                shared_state.telemetry_enabled = True
            elif cmd_id == command_defs.CMD_ID_DISABLE_TELEMETRY:
                print("CMD: Disable Telemetry")
                shared_state.telemetry_enabled = False
            elif cmd_id == command_defs.CMD_ID_RESTART_APP:
                print("CMD: Restart Application")
                shared_state.app_restart_requested = True
            elif cmd_id == command_defs.CMD_ID_SET_TELEMETRY_INTERVAL:
                if not payload: # Check if payload is empty
                    print("CMD ERR: SET_TELEMETRY_INTERVAL missing payload")
                    return
                try:
                    freq_hz = command_defs.unpack_set_interval_payload(payload)
                    print(f"CMD: Set Telemetry Interval to {freq_hz} Hz")
                    if freq_hz > 0:
                        shared_state.telemetry_interval_seconds = 1.0 / freq_hz
                        # Ensure telemetry is enabled if a valid positive frequency is set
                        # shared_state.telemetry_enabled = True # Optional: implicitly enable if interval is set
                        print(f"CMD INFO: Telemetry interval set to {shared_state.telemetry_interval_seconds} seconds.")
                    else:
                        # Consider disabling telemetry or setting a very long interval if freq is 0 or negative
                        print("CMD WARN: Telemetry frequency <= 0 Hz. Disabling telemetry.")
                        shared_state.telemetry_enabled = False # Or set a max interval
                except struct.error as e:
                    print(f"CMD ERR: Failed to unpack frequency for SET_TELEMETRY_INTERVAL: {e}")
                except ValueError as e: # From unpack_set_interval_payload if data too short
                    print(f"CMD ERR: Invalid payload for SET_TELEMETRY_INTERVAL: {e}")

            else:
                print(f"CMD ERR: Unknown Command ID: {hex(cmd_id)}")

        except ValueError as e: # From unpack_command_id if data too short
            print(f"CMD ERR: Could not parse command: {e}")
        except Exception as e:
            print(f"CMD ERR: Error processing command: {e}")

    def error_received(self, exc):
        print(f"Command UDP server error: {exc}")

    def connection_lost(self, exc):
        # This is not typically called for datagram (UDP) protocols as they are connectionless.
        # However, the base class might define it.
        print("Command UDP server connection supposedly lost (should not happen for UDP).")


async def start_command_listener():
    print("Starting UDP Command Listener...")
    loop = asyncio.get_running_loop() # In Python 3.7+
    
    # Ensure the transport and protocol are properly created and managed.
    # The `create_datagram_endpoint` is the correct high-level API.
    try:
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: CommandProtocol(),
            local_addr=(COMMAND_LISTEN_IP, COMMAND_LISTEN_PORT)
        )
    except OSError as e:
        print(f"Critical CMD ERR: Failed to bind command listener to {COMMAND_LISTEN_IP}:{COMMAND_LISTEN_PORT} - {e}")
        print("Check if the port is already in use or if there are network permission issues.")
        # Depending on the application's design, this might be a fatal error.
        # For now, we'll let it propagate or handle it by not running the listener.
        # This part of the code (start_command_listener) will not complete, so the task will end.
        # The main application logic needs to be aware if this task fails to start.
        return # Exit this coroutine if binding fails

    try:
        # Keep the listener running. asyncio.Future() creates a future that doesn't complete on its own.
        # This is a common way to keep a server-like task running until it's cancelled or an error occurs.
        await asyncio.Future()  
    except asyncio.CancelledError:
        print("Command listener task cancelled.") # Handle cancellation
    finally:
        print("Stopping UDP Command Listener...")
        if transport and not transport.is_closing():
            transport.close()

# Example of how this might be run (for testing, not for main app)
if __name__ == '__main__':
    # This is for standalone testing of the command listener.
    # In the main application, `start_command_listener` will be run as an asyncio task.
    async def main():
        # For testing, initialize shared_state or mock it if needed
        shared_state.telemetry_enabled = True
        shared_state.telemetry_interval_seconds = 5.0 
        print(f"Initial state: Telemetry enabled: {shared_state.telemetry_enabled}, Interval: {shared_state.telemetry_interval_seconds}s")
        
        listener_task = asyncio.create_task(start_command_listener())
        
        # Simulate running for a while, then stopping
        await asyncio.sleep(600) # Run for 10 minutes for testing
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            print("Listener task successfully cancelled in main example.")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Command listener test stopped by KeyboardInterrupt.")

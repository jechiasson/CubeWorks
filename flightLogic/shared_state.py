# flightLogic/shared_state.py
import asyncio

# Telemetry state
telemetry_enabled = True  # Global flag to enable/disable telemetry
telemetry_interval_seconds = 10.0  # Default telemetry interval (0.1 Hz)

# Application state
app_restart_requested = False # Global flag to signal application restart

# Lock for thread-safe/async-safe modification of shared state if needed.
# For asyncio applications where modifications are primarily from the main event
# loop or well-defined asyncio tasks, explicit locks for simple types like
# booleans and floats might not always be necessary. However, if there's any
# doubt or potential for race conditions (e.g., from different threads if those
# were ever introduced, or complex interactions between many tasks), a lock
# would be safer.
# For this implementation, we'll assume direct modification from asyncio tasks
# is acceptable as per the prompt's guidance.
# state_lock = asyncio.Lock() # Example if a lock were to be used

# Example of using the lock (if implemented):
# async def set_telemetry_status(status: bool):
#     async with state_lock:
#         global telemetry_enabled
#         telemetry_enabled = status

# async def get_telemetry_status() -> bool:
#     async with state_lock:
#         return telemetry_enabled

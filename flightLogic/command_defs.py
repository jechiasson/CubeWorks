import struct

# Command IDs (2-byte unsigned short, big-endian)
CMD_ID_ENABLE_TELEMETRY = 0x0001
CMD_ID_DISABLE_TELEMETRY = 0x0002
CMD_ID_RESTART_APP = 0x0003
CMD_ID_SET_TELEMETRY_INTERVAL = 0x0004

# Command packet structures (using struct format strings - big-endian)
# For commands without additional payload
SIMPLE_CMD_FORMAT = ">H"  # Header: Command ID (USHORT)

# For SET_TELEMETRY_INTERVAL command
# Header: Command ID (USHORT), Payload: Frequency (FLOAT, 4 bytes)
SET_INTERVAL_CMD_FORMAT = ">Hf"
SET_INTERVAL_CMD_PAYLOAD_FORMAT = ">f" # Just the frequency part for packing/unpacking payload

# Helper function (optional, but good for consistency)
def pack_simple_command(cmd_id: int) -> bytes:
    """Packs a command ID into a binary packet."""
    return struct.pack(SIMPLE_CMD_FORMAT, cmd_id)

def pack_set_interval_command(freq_hz: float) -> bytes:
    """Packs a SET_TELEMETRY_INTERVAL command with frequency."""
    return struct.pack(SET_INTERVAL_CMD_FORMAT, CMD_ID_SET_TELEMETRY_INTERVAL, freq_hz)

def unpack_command_id(data: bytes) -> tuple[int, bytes]:
    """Unpacks command ID from data, returns (cmd_id, remaining_data)."""
    if len(data) < struct.calcsize(SIMPLE_CMD_FORMAT):
        raise ValueError("Data too short to unpack command ID")
    cmd_id = struct.unpack_from(SIMPLE_CMD_FORMAT, data)[0]
    remaining_data = data[struct.calcsize(SIMPLE_CMD_FORMAT):]
    return cmd_id, remaining_data

def unpack_set_interval_payload(data: bytes) -> float:
    """Unpacks the frequency payload from a SET_TELEMETRY_INTERVAL command's remaining data."""
    if len(data) < struct.calcsize(SET_INTERVAL_CMD_PAYLOAD_FORMAT):
        raise ValueError("Data too short to unpack frequency payload")
    freq_hz = struct.unpack_from(SET_INTERVAL_CMD_PAYLOAD_FORMAT, data)[0]
    return freq_hz

# Example Usage (can be commented out or in an if __name__ == '__main__')
if __name__ == '__main__':
    enable_pkt = pack_simple_command(CMD_ID_ENABLE_TELEMETRY)
    print(f"Enable Telemetry Packet: {enable_pkt.hex()}")

    set_interval_pkt = pack_set_interval_command(0.5) # 0.5 Hz
    print(f"Set Interval Packet: {set_interval_pkt.hex()}")

    # Unpacking example
    parsed_cmd_id, _ = unpack_command_id(enable_pkt)
    print(f"Unpacked CMD_ID from enable_pkt: {hex(parsed_cmd_id)}")

    parsed_cmd_id_interval, payload_interval = unpack_command_id(set_interval_pkt)
    parsed_freq = unpack_set_interval_payload(payload_interval)
    print(f"Unpacked CMD_ID from set_interval_pkt: {hex(parsed_cmd_id_interval)}, Freq: {parsed_freq} Hz")

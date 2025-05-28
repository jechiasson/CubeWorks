import struct
import time
import math # For nan

# Packet ID constant (unsigned short)
PACKET_ID = 0x1234

# Expected sensor names and order for serialization.
# These names must correspond to keys in the telemetry_data dictionary.
# The timestamp 'RTC_TIMESTAMP' is handled separately for packing but expected in the input dict.
EXPECTED_SENSORS = [
    # Accelerometer (example keys if flattened)
    'ACCEL_X', 'ACCEL_Y', 'ACCEL_Z',
    # Magnetometer (example keys if flattened)
    'MAG_X', 'MAG_Y', 'MAG_Z',
    # Gyroscope (example keys if flattened, kept from original)
    'GYRO_X', 'GYRO_Y', 'GYRO_Z',
    # CPU Temperature
    'CPU_TEMP_C', # Assuming this key will be in the flattened data
    # UV Sensor
    'UV_INDEX',   # Assuming this key will be in the flattened data
    # EPS Telemetry Points
    'EPS_MCU_TEMP_C',
    'EPS_CELL1_TEMP_C',
    'EPS_CELL2_TEMP_C',
    'EPS_BUS_VOLTAGE_V',
    'EPS_BUS_CURRENT_A',
    'EPS_BCR_VOLTAGE_V',
    'EPS_BCR_CURRENT_A',
    'EPS_3V3_CURRENT_A',
    'EPS_5V_CURRENT_A',
    'EPS_SPX_VOLTAGE_V',
    'EPS_SPX_MINUS_CURRENT_A',
    'EPS_SPX_PLUS_CURRENT_A',
    'EPS_SPY_VOLTAGE_V',
    'EPS_SPY_MINUS_CURRENT_A',
    'EPS_SPY_PLUS_CURRENT_A',
    'EPS_SPZ_VOLTAGE_V',
    'EPS_SPZ_PLUS_CURRENT_A'
]
# Default value for missing sensors
DEFAULT_SENSOR_VALUE = math.nan # Using NaN for missing float values

def serialize_telemetry(telemetry_data: dict, output_file_path: str) -> bool:
    """
    Serializes telemetry data into a binary packet and appends it to a file.

    The binary packet structure is:
    1. Packet Length (4 bytes, unsigned int, big-endian) - This is the length of the (Packet ID + Timestamp + Sensor Data)
    2. Packet ID (2 bytes, unsigned short, big-endian)
    3. Timestamp (8 bytes, double, big-endian)
    4. Sensor Data (each as 4-byte float, big-endian, in the order of EXPECTED_SENSORS)

    Args:
        telemetry_data (dict): A dictionary containing telemetry readings.
                               It's expected to have a key for timestamp (e.g., 'RTC_TIMESTAMP')
                               and keys matching the names in EXPECTED_SENSORS.
        output_file_path (str): The path to the binary file where data should be appended.

    Returns:
        bool: True if serialization and writing were successful, False otherwise.
    """
    try:
        # a. Extract timestamp
        timestamp = telemetry_data.get('RTC_TIMESTAMP', time.time())

        # b. Prepare list of sensor values
        sensor_values = []
        for sensor_name in EXPECTED_SENSORS:
            value = telemetry_data.get(sensor_name, DEFAULT_SENSOR_VALUE)
            try:
                sensor_values.append(float(value))
            except (ValueError, TypeError):
                sensor_values.append(DEFAULT_SENSOR_VALUE)
        
        # c. Construct the binary packet (payload part: Packet ID, Timestamp, Sensor Values)
        payload_format = '>Hd' + 'f' * len(EXPECTED_SENSORS)
        
        binary_payload = struct.pack(payload_format, PACKET_ID, timestamp, *sensor_values)
        
        # d. Calculate total length of this binary packet (payload)
        payload_length = len(binary_payload)
        
        # e. Prepend the packet length (as a 4-byte unsigned integer, big-endian)
        length_prefix = struct.pack('>I', payload_length)
        
        # f. Open the output_file_path in append binary mode ('ab')
        with open(output_file_path, 'ab') as f:
            # g. Write the 4-byte length, then the binary packet
            f.write(length_prefix)
            f.write(binary_payload)
            
        return True

    except FileNotFoundError:
        print(f"Error: Output file path not found: {output_file_path}")
        return False
    except IOError as e:
        print(f"Error writing to file {output_file_path}: {e}")
        return False
    except struct.error as e:
        print(f"Error packing data: {e}. Check data types and format string.")
        print(f"Payload format: {payload_format}")
        print(f"Data for packing: ID={PACKET_ID}, TS={timestamp}, Values (first 5): {sensor_values[:5]}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during telemetry serialization: {e}")
        return False

if __name__ == '__main__':
    print("Testing telemetry_writer.py...")

    example_data = {
        'RTC_TIMESTAMP': time.time() + 1000, 
        'ACCEL_X': 1.1, 'ACCEL_Y': -2.2, 'ACCEL_Z': 3.3,
        'MAG_X': 0.1, 'MAG_Y': -0.2, 'MAG_Z': 0.3,
        'GYRO_X': 10.0, 'GYRO_Y': 20.0, 'GYRO_Z': 30.0, # Gyro data included
        'CPU_TEMP_C': 45.5,
        'UV_INDEX': 0.7,
        # EPS Data (matches keys from EPS.py's get_telemetry_data)
        'EPS_MCU_TEMP_C': 30.1,
        'EPS_CELL1_TEMP_C': 25.2,
        'EPS_CELL2_TEMP_C': 26.3,
        'EPS_BUS_VOLTAGE_V': 4.01,
        'EPS_BUS_CURRENT_A': 0.55,
        'EPS_BCR_VOLTAGE_V': 4.8,
        'EPS_BCR_CURRENT_A': 0.2,
        'EPS_3V3_CURRENT_A': 0.1,
        'EPS_5V_CURRENT_A': 0.15,
        'EPS_SPX_VOLTAGE_V': 5.0,
        'EPS_SPX_MINUS_CURRENT_A': 0.01,
        'EPS_SPX_PLUS_CURRENT_A': 0.02,
        'EPS_SPY_VOLTAGE_V': 5.1,
        'EPS_SPY_MINUS_CURRENT_A': 0.03,
        'EPS_SPY_PLUS_CURRENT_A': 0.04,
        'EPS_SPZ_VOLTAGE_V': 5.2,
        'EPS_SPZ_PLUS_CURRENT_A': 0.05
    }
    
    output_bin_file = "test_telemetry_output.bin"

    print(f"Serializing data: {example_data}")
    success = serialize_telemetry(example_data, output_bin_file)

    if success:
        print(f"Data successfully serialized and written to {output_bin_file}")
        try:
            with open(output_bin_file, 'rb') as f:
                length_bytes = f.read(4)
                if not length_bytes:
                    print("Verification failed: File is empty or length prefix missing.")
                else:
                    payload_len_read = struct.unpack('>I', length_bytes)[0]
                    print(f"Read payload length prefix: {payload_len_read} bytes")
                    
                    payload_read = f.read(payload_len_read)
                    if len(payload_read) != payload_len_read:
                        print(f"Verification failed: Expected to read {payload_len_read} bytes of payload, got {len(payload_read)}")
                    else:
                        num_sensors = len(EXPECTED_SENSORS)
                        expected_payload_format = '>Hd' + 'f' * num_sensors
                        
                        if struct.calcsize(expected_payload_format) != payload_len_read:
                             print(f"Verification warning: Calculated format size {struct.calcsize(expected_payload_format)} does not match read payload length {payload_len_read}")

                        unpacked_data = struct.unpack(expected_payload_format, payload_read)
                        
                        read_packet_id = unpacked_data[0]
                        read_timestamp = unpacked_data[1]
                        read_sensor_values = unpacked_data[2:]
                        
                        print(f"  Read Packet ID: {hex(read_packet_id)} (Expected: {hex(PACKET_ID)})")
                        print(f"  Read Timestamp: {read_timestamp} (Original: {example_data.get('RTC_TIMESTAMP')})")
                        print(f"  Read Sensor Values (first 5): {read_sensor_values[:5]}")
                        
                        if read_packet_id == PACKET_ID and \
                           abs(read_timestamp - example_data.get('RTC_TIMESTAMP')) < 0.001 and \
                           abs(read_sensor_values[0] - example_data['ACCEL_X']) < 0.001:
                            print("Basic verification successful!")
                        else:
                            print("Basic verification FAILED.")
        except Exception as e:
            print(f"Error during verification: {e}")
    else:
        print("Serialization failed.")

    print("\nTelemetry_writer.py tests (with updated EXPECTED_SENSORS) finished.")

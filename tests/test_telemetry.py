import unittest
import sys
import json
import asyncio
from unittest.mock import Mock, patch, mock_open, MagicMock

# Adjust path to import from flightLogic and Drivers
sys.path.append('../') # Assuming tests are run from the 'tests' directory
from flightLogic.telemetryManager import TelemetryManager
# For mainFlightLogic tests, we might need to patch modules it imports, or the module itself.
# We'll try to import specific components if possible, otherwise patch broadly.
# For now, we will patch objects within mainFlightLogic as it's executed.
import flightLogic.mainFlightLogic as mainFlightLogic_module

# Mock Driver for testing TelemetryManager
class MockDriver:
    def __init__(self, name, telemetry_value={"value": 123}):
        self.name = name
        self._telemetry_value = telemetry_value
        self.get_telemetry_data_call_count = 0 # Manual call count tracking

    def get_telemetry_data(self):
        self.get_telemetry_data_call_count += 1
        return {f"{self.name}_data": self._telemetry_value}

class TestTelemetryManager(unittest.TestCase):

    def test_register_driver_enabled(self):
        # print("\nRunning test_register_driver_enabled")
        mock_driver_instance = MockDriver("SensorA")
        enabled_list = ["SensorA"]
        tm = TelemetryManager(enabled_sensors_list=enabled_list)
        tm.register_driver(mock_driver_instance)
        self.assertIn(mock_driver_instance, tm.drivers)
        # print("test_register_driver_enabled PASSED")

    def test_register_driver_not_enabled(self):
        # print("\nRunning test_register_driver_not_enabled")
        mock_driver_instance = MockDriver("SensorB")
        enabled_list = ["SensorA"] # SensorB is not in this list
        tm = TelemetryManager(enabled_sensors_list=enabled_list)
        tm.register_driver(mock_driver_instance)
        self.assertNotIn(mock_driver_instance, tm.drivers)
        # print("test_register_driver_not_enabled PASSED")

    def test_register_driver_no_name_attribute(self):
        # print("\nRunning test_register_driver_no_name_attribute")
        class NoNameDriver: # Doesn't have a 'name' attribute
            def get_telemetry_data(self): return {"data": 1}
        
        no_name_driver_instance = NoNameDriver()
        enabled_list = ["NoNameDriverShouldStillNotBeRegistered"] 
        tm = TelemetryManager(enabled_sensors_list=enabled_list)
        tm.register_driver(no_name_driver_instance) 
        self.assertNotIn(no_name_driver_instance, tm.drivers)
        # print("test_register_driver_no_name_attribute PASSED")

    def test_register_multiple_drivers(self):
        # print("\nRunning test_register_multiple_drivers")
        driver1 = MockDriver("SensorA")
        driver2 = MockDriver("SensorC")
        driver3 = MockDriver("SensorD") # Not enabled
        enabled_list = ["SensorA", "SensorC"]
        tm = TelemetryManager(enabled_sensors_list=enabled_list)
        tm.register_driver(driver1)
        tm.register_driver(driver2)
        tm.register_driver(driver3)
        self.assertIn(driver1, tm.drivers)
        self.assertIn(driver2, tm.drivers)
        self.assertNotIn(driver3, tm.drivers)
        self.assertEqual(len(tm.drivers), 2)
        # print("test_register_multiple_drivers PASSED")

    def test_register_driver_duplicate(self):
        # print("\nRunning test_register_driver_duplicate")
        mock_driver_instance = MockDriver("SensorA")
        enabled_list = ["SensorA"]
        tm = TelemetryManager(enabled_sensors_list=enabled_list)
        tm.register_driver(mock_driver_instance)
        tm.register_driver(mock_driver_instance) # Try registering again
        self.assertEqual(len(tm.drivers), 1)
        self.assertIn(mock_driver_instance, tm.drivers)
        # print("test_register_driver_duplicate PASSED")

    def test_collect_telemetry_single_driver(self):
        # print("\nRunning test_collect_telemetry_single_driver")
        driver = MockDriver("SensorX", telemetry_value={"temp": 42})
        enabled_list = ["SensorX"]
        tm = TelemetryManager(enabled_sensors_list=enabled_list)
        tm.register_driver(driver)
        telemetry = tm.collect_telemetry()
        expected_telemetry = {"SensorX_data": {"temp": 42}}
        self.assertEqual(telemetry, expected_telemetry)
        # print("test_collect_telemetry_single_driver PASSED")

    def test_collect_telemetry_multiple_drivers(self):
        # print("\nRunning test_collect_telemetry_multiple_drivers")
        driver1 = MockDriver("SensorX", telemetry_value={"temp": 42})
        driver2 = MockDriver("SensorY", telemetry_value={"humidity": 88})
        enabled_list = ["SensorX", "SensorY"]
        tm = TelemetryManager(enabled_sensors_list=enabled_list)
        tm.register_driver(driver1)
        tm.register_driver(driver2)
        telemetry = tm.collect_telemetry()
        expected_telemetry = {
            "SensorX_data": {"temp": 42},
            "SensorY_data": {"humidity": 88}
        }
        self.assertEqual(telemetry, expected_telemetry)
        # print("test_collect_telemetry_multiple_drivers PASSED")

    def test_collect_telemetry_no_drivers_registered(self):
        # print("\nRunning test_collect_telemetry_no_drivers_registered")
        tm = TelemetryManager(enabled_sensors_list=["SensorX"])
        telemetry = tm.collect_telemetry()
        self.assertEqual(telemetry, {})
        # print("test_collect_telemetry_no_drivers_registered PASSED")

    def test_collect_telemetry_driver_get_data_called(self):
        # print("\nRunning test_collect_telemetry_driver_get_data_called")
        mock_driver_obj = Mock()
        mock_driver_obj.name = "MockSensor"
        mock_driver_obj.get_telemetry_data.return_value = {"MockSensor_data": {"voltage": 5}}
        
        enabled_list = ["MockSensor"]
        tm = TelemetryManager(enabled_sensors_list=enabled_list)
        tm.register_driver(mock_driver_obj)
        telemetry_data = tm.collect_telemetry()
        mock_driver_obj.get_telemetry_data.assert_called_once()
        self.assertEqual(telemetry_data, {"MockSensor_data": {"voltage": 5}})
        # print("test_collect_telemetry_driver_get_data_called PASSED")

    def test_telemetry_manager_init_empty_or_none_list(self):
        # print("\nRunning test_telemetry_manager_init_empty_or_none_list")
        tm_none = TelemetryManager(enabled_sensors_list=None)
        self.assertEqual(tm_none.enabled_sensors, [])
        driver_a = MockDriver("SensorA")
        tm_none.register_driver(driver_a)
        self.assertNotIn(driver_a, tm_none.drivers)

        tm_empty = TelemetryManager(enabled_sensors_list=[])
        self.assertEqual(tm_empty.enabled_sensors, [])
        tm_empty.register_driver(driver_a)
        self.assertNotIn(driver_a, tm_empty.drivers)
        # print("test_telemetry_manager_init_empty_or_none_list PASSED")

    def test_collect_telemetry_bad_drivers(self):
        # print("\nRunning test_collect_telemetry_bad_drivers")
        class BadReturnDriver(MockDriver):
            def get_telemetry_data(self):
                super().get_telemetry_data() 
                return "not a dictionary"

        class MissingMethodDriver:
            def __init__(self, name): self.name = name

        driver_bad_return = BadReturnDriver("BadReturnSensor", {})
        driver_missing_method = MissingMethodDriver("MissingMethodSensor")
        enabled_list = ["BadReturnSensor", "MissingMethodSensor"]
        tm = TelemetryManager(enabled_sensors_list=enabled_list)
        tm.register_driver(driver_bad_return)
        tm.register_driver(driver_missing_method)
        
        with patch('builtins.print') as mocked_print:
            telemetry = tm.collect_telemetry()
            self.assertEqual(telemetry, {})
            self.assertTrue(any("Warning: Driver" in call.args[0] and "did not return a dictionary" in call.args[0] for call in mocked_print.call_args_list))
            self.assertTrue(any("Warning: Driver" in call.args[0] and "does not have a get_telemetry_data method" in call.args[0] for call in mocked_print.call_args_list))
        # print("test_collect_telemetry_bad_drivers PASSED")

# Tests for mainFlightLogic.py telemetry integration
@patch('flightLogic.mainFlightLogic.saveTofiles') # Mock the saveTofiles module
@patch('flightLogic.mainFlightLogic.getDriverData') # Mock the getDriverData module
@patch('flightLogic.mainFlightLogic.pythonInterrupt') # Mock the pythonInterrupt module
@patch('flightLogic.mainFlightLogic.packetProcessing') # Mock packetProcessing
@patch('flightLogic.mainFlightLogic.antennaDoor') # Mock antennaDoor (original class)
@patch('flightLogic.mainFlightLogic.EPS') # Mock original EPS class
@patch('flightLogic.mainFlightLogic.Camera') # Mock original Camera class
@patch('flightLogic.mainFlightLogic.FileReset') # Mock FileReset
@patch('flightLogic.mainFlightLogic.heart_beat') # Mock heart_beat
# Mock mission mode classes
@patch('flightLogic.mainFlightLogic.antennaMode')
@patch('flightLogic.mainFlightLogic.preBoomMode')
@patch('flightLogic.mainFlightLogic.boomMode')
@patch('flightLogic.mainFlightLogic.postBoomMode')
@patch('flightLogic.mainFlightLogic.Transmitting')
class TestMainFlightLogicTelemetryIntegration(unittest.TestCase):

    # Patch all driver imports within mainFlightLogic.py to control their instantiation
    @patch('flightLogic.mainFlightLogic.Accelerometer', new_callable=MagicMock)
    @patch('flightLogic.mainFlightLogic.Magnetometer', new_callable=MagicMock)
    @patch('flightLogic.mainFlightLogic.UVDriver', new_callable=MagicMock)
    @patch('flightLogic.mainFlightLogic.ADC', new_callable=MagicMock)
    @patch('flightLogic.mainFlightLogic.antennaDoorDriver', new_callable=MagicMock) # Alias for AntennaDoor
    @patch('flightLogic.mainFlightLogic.BackupAntennaDeployer', new_callable=MagicMock)
    @patch('flightLogic.mainFlightLogic.BoomDeployer', new_callable=MagicMock)
    @patch('flightLogic.mainFlightLogic.CameraDriver', new_callable=MagicMock) # Alias for Camera
    @patch('flightLogic.mainFlightLogic.CpuTemperature', new_callable=MagicMock)
    @patch('flightLogic.mainFlightLogic.EPSDriver', new_callable=MagicMock) # Alias for EPS
    @patch('flightLogic.mainFlightLogic.RTC', new_callable=MagicMock)
    @patch('flightLogic.mainFlightLogic.TempSensor', new_callable=MagicMock)
    @patch('flightLogic.mainFlightLogic.sunSensor', new_callable=MagicMock)
    @patch('flightLogic.mainFlightLogic.TransceiverConfig', new_callable=MagicMock)
    @patch('flightLogic.mainFlightLogic.TelemetryManager', new_callable=MagicMock) # Mock TelemetryManager class itself
    @patch('flightLogic.mainFlightLogic.asyncio.create_task', new_callable=MagicMock) # Mock asyncio.create_task
    @patch('flightLogic.mainFlightLogic.collect_and_log_telemetry') # Mock the coroutine function
    def run_execute_flight_logic_with_mocks(self, mock_config_data, mock_collect_and_log_telemetry, mock_create_task, MockTelemetryManager, *other_driver_mocks):
        """
        Helper function to run the core part of executeFlightLogic with extensive mocking.
        `mock_config_data` can be a dict for successful load, FileNotFoundError, or JSONDecodeError.
        """
        # Mock open for /home/pi/lastBase.txt
        mock_base_file = mock_open(read_data='0') # Default base value
        
        # Mock os.path.join for config file path construction
        # This is important because mainFlightLogic uses os.path.join to build the config path
        with patch('os.path.join', return_value="/mocked/config/path/telemetry_config.json"):
            # Mock `open` for the telemetry config file
            if isinstance(mock_config_data, FileNotFoundError):
                m_open = mock_open()
                m_open.side_effect = FileNotFoundError
            elif isinstance(mock_config_data, json.JSONDecodeError):
                # Simulate read that will cause JSONDecodeError
                m_open = mock_open(read_data="invalid json")
            else: # dict
                m_open = mock_open(read_data=json.dumps(mock_config_data))

            with patch('builtins.open', m_open) as patched_open:
                # Ensure lastBase.txt uses the specific mock_base_file
                def open_side_effect(file, mode='r'):
                    if file == "/home/pi/lastBase.txt":
                        return mock_base_file.return_value
                    elif file == "/mocked/config/path/telemetry_config.json":
                        # This will trigger the side_effect for config file if m_open was configured with one
                        return m_open.return_value 
                    # For bootRecords.txt and backupBootRecords.txt, allow actual operations or use more mocks
                    # For simplicity here, we'll let them pass through if not explicitly mocked,
                    # but in a real scenario, they might need specific handling if `readData` / `recordData` are complex.
                    # For now, we assume readData/recordData are simple or also mocked/irrelevant to telemetry setup.
                    # We can mock them to prevent file IO during tests
                    # For now, let's add a pass-through for other files or specific mocks if issues arise.
                    # This example will focus on telemetry config loading.
                    # For bootRecords, let's mock them to prevent file system side effects.
                    elif "bootRecords.txt" in file:
                        return mock_open(read_data="0\n0\n0\n").return_value # Default boot record
                    return m_open.return_value # Fallback, should ideally be more specific

                patched_open.side_effect = open_side_effect
                
                # Mock readData and recordData to avoid file I/O complexities not central to this test
                with patch('flightLogic.mainFlightLogic.readData', return_value=(0, False, 0)), \
                     patch('flightLogic.mainFlightLogic.recordData'):
                    # We need to run the async function executeFlightLogic
                    # Since it's async and has an infinite loop, we can't run it directly till completion.
                    # We'll run parts or use a test runner that handles async code better if needed.
                    # For now, let's focus on the setup part by calling it and letting it run enough
                    # for telemetry setup.
                    # This is tricky; ideally, the setup logic would be in a separable synchronous function.
                    # We'll assume the setup happens before the first await asyncio.sleep() in the main logic.
                    # To test the setup, we don't need the full loop.
                    # A better way would be to refactor mainFlightLogic.
                    # For now, we'll rely on patching to control flow and check calls.
                    
                    # Execute the function. It will run until the first `await` that isn't mocked away,
                    # or if parts are refactored. Since many `await` calls relate to mission modes
                    # which are heavily mocked, the initial setup including telemetry should run.
                    try:
                        asyncio.run(mainFlightLogic_module.executeFlightLogic())
                    except Exception as e:
                        # This is expected if the function has an infinite loop
                        # or tries to run parts we haven't fully mocked for a long-running test.
                        # We are interested in the calls made during the setup phase.
                        # print(f"executeFlightLogic threw an expected exception during test run: {e}")
                        pass


    def test_load_telemetry_config_file_found(self, MockFileReset, MockTransmitting, MockPostBoom, MockBoom, MockPreBoom, MockAntenna, MockHB, MockCamera, MockEPS, MockAntennaDoorOrg, MockPacketProc, MockPyInterrupt, MockGetDriver, MockSaveTo):
        print("\nRunning test_load_telemetry_config_file_found")
        sample_config = {"telemetry_interval_seconds": 30, "enabled_sensors": ["SensorA", "SensorB"]}
        
        # We need to get the mock_telemetry_manager_instance created inside run_execute_flight_logic
        # This is done by accessing the MockTelemetryManager.return_value
        mock_tm_instance = mainFlightLogic_module.TelemetryManager.return_value 

        self.run_execute_flight_logic_with_mocks(sample_config)

        # Assert TelemetryManager was called with the correct enabled_sensors_list
        mainFlightLogic_module.TelemetryManager.assert_called_once_with(enabled_sensors_list=["SensorA", "SensorB"])
        
        # Assert that create_task was called for telemetry
        # Check if collect_and_log_telemetry was called with the correct interval
        # The second argument to collect_and_log_telemetry is the interval
        # This requires inspecting the arguments of the call to asyncio.create_task
        # The first argument to create_task is the coroutine object
        found_telemetry_task_call = False
        for call_args in mainFlightLogic_module.asyncio.create_task.call_args_list:
            task_coro = call_args[0][0] # The coroutine is the first positional argument to create_task
            # Check if this is the telemetry coroutine by checking its arguments
            # This is a bit indirect. We mock `collect_and_log_telemetry` so we can check its call.
            if mainFlightLogic_module.collect_and_log_telemetry.is_coroutine: # Check if it's the right mock
                 mainFlightLogic_module.collect_and_log_telemetry.assert_any_call(mock_tm_instance, 30)
                 found_telemetry_task_call = True
                 break
        self.assertTrue(found_telemetry_task_call, "Telemetry task with correct interval not started.")
        print("test_load_telemetry_config_file_found PASSED")


    def test_load_telemetry_config_file_not_found(self, MockFileReset, MockTransmitting, MockPostBoom, MockBoom, MockPreBoom, MockAntenna, MockHB, MockCamera, MockEPS, MockAntennaDoorOrg, MockPacketProc, MockPyInterrupt, MockGetDriver, MockSaveTo):
        print("\nRunning test_load_telemetry_config_file_not_found")
        mock_tm_instance = mainFlightLogic_module.TelemetryManager.return_value
        self.run_execute_flight_logic_with_mocks(FileNotFoundError())

        # Assert TelemetryManager was called with default enabled_sensors list
        default_list = ["Accelerometer", "Magnetometer", "EPS", "CpuTemperature"]
        mainFlightLogic_module.TelemetryManager.assert_called_once_with(enabled_sensors_list=default_list)
        
        # Assert telemetry task started with default interval (60)
        found_telemetry_task_call = False
        for call_args in mainFlightLogic_module.asyncio.create_task.call_args_list:
            task_coro = call_args[0][0]
            if mainFlightLogic_module.collect_and_log_telemetry.is_coroutine:
                 mainFlightLogic_module.collect_and_log_telemetry.assert_any_call(mock_tm_instance, 60)
                 found_telemetry_task_call = True
                 break
        self.assertTrue(found_telemetry_task_call, "Telemetry task with default interval not started.")
        print("test_load_telemetry_config_file_not_found PASSED")

    def test_load_telemetry_config_invalid_json(self, MockFileReset, MockTransmitting, MockPostBoom, MockBoom, MockPreBoom, MockAntenna, MockHB, MockCamera, MockEPS, MockAntennaDoorOrg, MockPacketProc, MockPyInterrupt, MockGetDriver, MockSaveTo):
        print("\nRunning test_load_telemetry_config_invalid_json")
        mock_tm_instance = mainFlightLogic_module.TelemetryManager.return_value
        self.run_execute_flight_logic_with_mocks(json.JSONDecodeError("Error", "doc", 0))

        default_list = ["Accelerometer", "Magnetometer", "EPS", "CpuTemperature"]
        mainFlightLogic_module.TelemetryManager.assert_called_once_with(enabled_sensors_list=default_list)
        
        found_telemetry_task_call = False
        for call_args in mainFlightLogic_module.asyncio.create_task.call_args_list:
            task_coro = call_args[0][0]
            if mainFlightLogic_module.collect_and_log_telemetry.is_coroutine:
                 mainFlightLogic_module.collect_and_log_telemetry.assert_any_call(mock_tm_instance, 60)
                 found_telemetry_task_call = True
                 break
        self.assertTrue(found_telemetry_task_call, "Telemetry task with default interval not started on JSON error.")
        print("test_load_telemetry_config_invalid_json PASSED")
        
    def test_drivers_instantiated_based_on_config(self, MockFileReset, MockTransmitting, MockPostBoom, MockBoom, MockPreBoom, MockAntenna, MockHB, MockCamera, MockEPS, MockAntennaDoorOrg, MockPacketProc, MockPyInterrupt, MockGetDriver, MockSaveTo):
        print("\nRunning test_drivers_instantiated_based_on_config")
        # Config enables only Accelerometer and EPS
        config = {"telemetry_interval_seconds": 60, "enabled_sensors": ["Accelerometer", "EPS"]}
        
        # Get the mock objects for specific drivers from the decorator arguments
        # The order of mocks in decorator is from bottom up, so last @patch is first arg.
        # We need to find the correct mock from `other_driver_mocks` or by inspecting the mock objects.
        # For simplicity, let's assume `other_driver_mocks` contains them in the order of patching.
        # The patching order is: Acc, Mag, UV, ADC, ... TransceiverConfig, TelemetryManager
        # So, MockAccelerometer will be other_driver_mocks[0], MockMagnetometer other_driver_mocks[1], etc.
        # This is fragile. A better way is to access them by the names used in @patch.
        # Example: mainFlightLogic_module.Accelerometer (which is the mock itself)
        
        self.run_execute_flight_logic_with_mocks(config)

        mainFlightLogic_module.Accelerometer.assert_called_once()
        mainFlightLogic_module.EPSDriver.assert_called_once() # EPS is aliased to EPSDriver
        mainFlightLogic_module.Magnetometer.assert_not_called()
        mainFlightLogic_module.UVDriver.assert_not_called()
        # ... and so on for other drivers that should not have been called.
        # This requires all patched drivers to be accessible.
        
        # Check that TelemetryManager.register_driver was called for the instances of enabled drivers
        # This is complex because we need to check it was called with an *instance* of Accelerometer,
        # and an *instance* of EPSDriver.
        # The TelemetryManager mock instance is mainFlightLogic_module.TelemetryManager.return_value
        tm_instance_mock = mainFlightLogic_module.TelemetryManager.return_value
        
        # Check calls to register_driver
        # Expected calls with specific driver instances.
        # The driver instances are themselves mocks: mainFlightLogic_module.Accelerometer.return_value
        # and mainFlightLogic_module.EPSDriver.return_value
        
        # We need to ensure that the register_driver was called with the correct mock instances
        # This can be tricky if the instance is created deep inside.
        # However, our driver_config_map logic instantiates them directly.
        
        # Check if register_driver was called with the instance of Accelerometer
        # This is simplified because TelemetryManager itself is mocked.
        # The actual registration logic is in TelemetryManager, here we check if mainFlightLogic
        # passed the right instances to its `register_driver` method.
        
        # The actual instances created are mainFlightLogic_module.Accelerometer.return_value, etc.
        # Check that register_driver was called with these.
        # This test is more about whether mainFlightLogic *attempted* to register them.
        # The TelemetryManager (mocked here) would then internally decide based on its enabled_list.
        
        # Given the structure, the loop in mainFlightLogic calls `telemetry_mgr.register_driver(driver_instance)`
        # So tm_instance_mock.register_driver should have been called.
        
        calls_to_register = tm_instance_mock.register_driver.call_args_list
        registered_driver_instances = [call[0][0] for call in calls_to_register] # get the first arg of each call

        self.assertIn(mainFlightLogic_module.Accelerometer.return_value, registered_driver_instances)
        self.assertIn(mainFlightLogic_module.EPSDriver.return_value, registered_driver_instances)
        self.assertEqual(len(registered_driver_instances), 2) # Only 2 drivers should be registered

        print("test_drivers_instantiated_based_on_config PASSED")


if __name__ == '__main__':
    print("Starting Telemetry Tests...")
    # unittest.main(verbosity=0) # verbosity=0 for less output, default is 1
    # Need to ensure the test loader picks up both classes.
    # Or run specific test suites.
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTelemetryManager))
    suite.addTest(unittest.makeSuite(TestMainFlightLogicTelemetryIntegration))
    runner = unittest.TextTestRunner(verbosity=2) # verbosity=2 for detailed output
    runner.run(suite)
    print("\nFinished Telemetry Tests.")

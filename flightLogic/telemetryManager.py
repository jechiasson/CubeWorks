class TelemetryManager:
    def __init__(self, enabled_sensors_list=None):
        """
        Initializes the TelemetryManager.

        Args:
            enabled_sensors_list (list, optional): A list of sensor names that should be registered.
                                                   If None or empty, no drivers will be registered through
                                                   the name-based filtering in register_driver.
                                                   Defaults to None.
        """
        self.drivers = []
        # If enabled_sensors_list is None, default to an empty list.
        # This means if no list is provided, no drivers will pass the name check in register_driver.
        self.enabled_sensors = enabled_sensors_list if enabled_sensors_list is not None else []
        if not self.enabled_sensors:
            print("TelemetryManager initialized with no enabled sensors specified. No drivers will be registered by name.")

    def register_driver(self, driver):
        """
        Registers a new driver with the TelemetryManager if its name is in the enabled_sensors list.

        Args:
            driver: The driver object to register. Must have a 'name' attribute.
        """
        if not hasattr(driver, 'name'):
            print(f"Driver {type(driver).__name__} cannot be registered: missing 'name' attribute.")
            return

        if driver.name in self.enabled_sensors:
            if driver not in self.drivers:
                self.drivers.append(driver)
                print(f"Driver '{driver.name}' registered.")
            else:
                print(f"Driver '{driver.name}' already registered.")
        else:
            print(f"Driver '{driver.name}' not in enabled_sensors list, not registered.")

    def collect_telemetry(self):
        """
        Collects telemetry data from all registered drivers.

        Assumes each driver object has a 'get_telemetry_data' method
        that returns a dictionary of its telemetry data.
        The keys in the returned dictionary should ideally be unique
        across drivers or namespaced to avoid collisions.
        Alternatively, this method could store data under a key
        representing the driver itself (e.g., driver.__class__.__name__).
        For this initial implementation, it will merge the dictionaries,
        potentially overwriting keys if not unique.
        """
        collected_data = {}
        for driver in self.drivers:
            try:
                data = driver.get_telemetry_data()
                if isinstance(data, dict):
                    collected_data.update(data)
                else:
                    # Handle cases where get_telemetry_data might not return a dict
                    # Or log a warning/error
                    print(f"Warning: Driver {driver} did not return a dictionary.")
            except AttributeError:
                # Handle cases where driver doesn't have get_telemetry_data
                # Or log a warning/error
                print(f"Warning: Driver {driver} does not have a get_telemetry_data method.")
            except Exception as e:
                # Catch any other errors during telemetry collection from a driver
                print(f"Error collecting telemetry from driver {driver}: {e}")
        return collected_data

# Example Usage (primarily for testing and illustration)
if __name__ == '__main__':
    # Dummy driver classes for testing
    class DummySensorDriver:
        def __init__(self, name):
            self.name = name # Crucial for registration filtering
            self.data_point = 0

        def get_telemetry_data(self):
            self.data_point += 1
            return {f"{self.name}_temperature": 20 + self.data_point, f"{self.name}_pressure": 1000 + self.data_point}

    class AnotherDummySensorDriver:
        # This driver will NOT be registered if filtering by name, as it lacks a .name attribute by default
        # Let's add a name attribute for testing the filtering
        def __init__(self, driver_name, sensor_id):
            self.name = driver_name 
            self.sensor_id = sensor_id
            self.value = 50

        def get_telemetry_data(self):
            self.value += 5
            return {f"sensor_{self.sensor_id}_value": self.value}

    class UnnamedSensorDriver: # This driver has no name attribute
        def get_telemetry_data(self):
            return {"unnamed_data": 100}


    # Test Case 1: No enabled_sensors_list provided (should register nothing by name)
    print("\n--- Test Case 1: No enabled_sensors_list ---")
    telemetry_mgr_empty = TelemetryManager() # or TelemetryManager(None) or TelemetryManager([])
    sensor_alpha_1 = DummySensorDriver("Alpha")
    sensor_beta_1 = AnotherDummySensorDriver("BetaSensor", "B75")
    telemetry_mgr_empty.register_driver(sensor_alpha_1)
    telemetry_mgr_empty.register_driver(sensor_beta_1)
    print(f"Number of drivers registered: {len(telemetry_mgr_empty.drivers)}")
    telemetry_output_empty = telemetry_mgr_empty.collect_telemetry()
    print("Collected Telemetry (empty list):", telemetry_output_empty)


    # Test Case 2: With an enabled_sensors_list
    print("\n--- Test Case 2: With enabled_sensors_list ---")
    enabled_list = ["Alpha", "Gamma"] # BetaSensor will be skipped
    telemetry_mgr_filtered = TelemetryManager(enabled_sensors_list=enabled_list)

    sensor_alpha_2 = DummySensorDriver("Alpha") # Should be registered
    sensor_beta_2 = AnotherDummySensorDriver("BetaSensor", "B75") # Should be skipped
    sensor_gamma_2 = DummySensorDriver("Gamma") # Should be registered
    unnamed_sensor = UnnamedSensorDriver() # Should be skipped (no name attribute)


    telemetry_mgr_filtered.register_driver(sensor_alpha_2)
    telemetry_mgr_filtered.register_driver(sensor_beta_2)
    telemetry_mgr_filtered.register_driver(sensor_gamma_2)
    telemetry_mgr_filtered.register_driver(unnamed_sensor)


    # Test registering the same driver again (Alpha)
    telemetry_mgr_filtered.register_driver(sensor_alpha_2)
    print(f"Number of drivers registered: {len(telemetry_mgr_filtered.drivers)}")


    # Collect telemetry data
    telemetry_output_filtered = telemetry_mgr_filtered.collect_telemetry()
    print("Collected Telemetry (filtered list):", telemetry_output_filtered)

    # Test a driver that doesn't return a dict (but is enabled)
    print("\n--- Test Case 3: Bad driver (but enabled) ---")
    class BadDriverNoDict:
        def __init__(self, name):
            self.name = name
        def get_telemetry_data(self):
            return "This is not a dictionary"

    telemetry_mgr_bad_driver = TelemetryManager(enabled_sensors_list=["BadOne"])
    bad_driver_1 = BadDriverNoDict("BadOne")
    telemetry_mgr_bad_driver.register_driver(bad_driver_1)
    telemetry_output_bad = telemetry_mgr_bad_driver.collect_telemetry()
    print("Collected Telemetry (with bad_driver_1):", telemetry_output_bad)


    # Test a driver that's missing the get_telemetry_data method (but is enabled)
    print("\n--- Test Case 4: Driver missing method (but enabled) ---")
    class BadDriverNoMethod:
        def __init__(self, name):
            self.name = name
        # No get_telemetry_data method

    telemetry_mgr_no_method = TelemetryManager(enabled_sensors_list=["NoMethodSensor"])
    bad_driver_2 = BadDriverNoMethod("NoMethodSensor")
    telemetry_mgr_no_method.register_driver(bad_driver_2)
    telemetry_output_no_method = telemetry_mgr_no_method.collect_telemetry()
    print("Collected Telemetry (with bad_driver_2):", telemetry_output_no_method)

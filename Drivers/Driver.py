import asyncio

class Driver:
    """
    Abstract class that defines a device driver.  
    """
    def __init__(self, name, delay=1, initial_delay=0):
        """
        Initializes a Driver object.
        1. self.name is a string identifying the object.
        2. self.delay is an integer defining the refresh frequency of the driver.
        3. self.initial_delay defines how long the driver should wait before beginning to refresh
        """
        self.name = name
        self.delay = delay
        self.initial_delay = initial_delay

    def read(self):
        """
        Abstract method that defines the behavior of the device driver.
        The child class implements this for communicating with specific hardware components.  
        """
        pass

    async def run(self, context, lock):
        """
        Asynchronous method that controls how often driver reads values from the hardware component.
        Waits self.initial_delay time before beginning to read from the hardware.
        1. context is the mission mode defined in the mission_modes module and passed to the driver by main.
        2. lock controls asynchronous execution to avoid race conditions.
        """
        if self.initial_delay > 0:
            await asyncio.sleep(self.initial_delay)
            self.initial_delay = 0

        while True:
            reading = self.read()
            async with lock:
                context[self.name] = reading
            await asyncio.sleep(self.delay)

    def get_telemetry_data(self):
        """
        Reads data from the driver and formats it for telemetry.
        Returns:
            dict: A dictionary containing the driver's name and its read value.
                  Returns {'driver_name': self.name, 'value': None} if read() fails or returns None.
        """
        value = None
        try:
            value = self.read()
        except Exception as e:
            # Optionally log the error e
            # print(f"Error reading from driver {self.name}: {e}")
            pass  # Value remains None

        try:
            # self.name should always exist due to __init__
            return {'driver_name': self.name, 'value': value}
        except AttributeError:
            # Fallback if self.name is somehow not set, though unlikely.
            return {'driver_name': 'UnknownDriver', 'value': value}

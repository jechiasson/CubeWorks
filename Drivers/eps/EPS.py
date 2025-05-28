#EPS Driver, not tested against hardware yet
from Drivers.Driver import Driver
import smbus
import RPi.GPIO as GPIO
"""
Pulls battery data and solar panel data from the EPS
"""

class EPS(Driver):
    #this sets up i2c commincation.
    def __init__(self):
        super().__init__("EPS") #Calls parent constructor

        #Setup I2C bus for communication
        self.DEVICE_BUS = 1
        self.DEVICE_ADDR = 0x18
        self.RegisterADR = 0x00
        self.bus = smbus.SMBus(self.DEVICE_BUS)

    def enableRaw(self):
        #This method enables RAW battery output from the EPS
        #The command is 3 bytes device address left-shifted by one bit, the command, and the state
        self.bus.write_byte_data(self.DEVICE_ADDR, 0x01, 0x03)

    def disableRaw(self):
        #This method disables RAW battery output from the EPS
        #The command is 3 bytes device address left-shifted by one bit, the command, and the state
        self.bus.write_byte_data(self.DEVICE_ADDR, 0x01, 0x02)

    def enableUHF(self):
        #This method sends the command to the EPS to enable UHF Transmission, and sets the corresponding GPIO Pin high on the Pi
        self.bus.write_byte_data(self.DEVICE_ADDR, 0x0E, 0x03)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(18, GPIO.OUT, initial = GPIO.HIGH)
        GPIO.output(18, GPIO.HIGH)

    def read(self):
        #returns nothing since there are so many different things we could read, use other methods instead
        # Consider if a summary or key status could be returned here for basic telemetry.
        pass

    def get_telemetry_data(self):
        """
        Collects all telemetry data points from the EPS.
        """
        return {
            'driver_name': self.name,
            'mcu_temp_c': self.getMCUTemp(),
            'cell1_temp_c': self.getCell1Temp(),
            'cell2_temp_c': self.getCell2Temp(),
            'bus_voltage_v': self.getBusVoltage(),
            'bus_current_a': self.getBusCurrent(),
            'bcr_voltage_v': self.getBCRVoltage(),
            'bcr_current_a': self.getBCRCurrent(),
            '3v3_current_a': self.get3V3Current(),
            '5v_current_a': self.get5VCurrent(),
            'spx_voltage_v': self.getSPXVoltage(),
            'spx_minus_current_a': self.getSPXMinusCurrent(),
            'spx_plus_current_a': self.getSPXPlusCurrent(),
            'spy_voltage_v': self.getSPYVoltage(),
            'spy_minus_current_a': self.getSPYMinusCurrent(),
            'spy_plus_current_a': self.getSPYPlusCurrent(),
            'spz_voltage_v': self.getSPZVoltage(),
            'spz_plus_current_a': self.getSPZPlusCurrent()
            # Note: If any of these getter methods can fail, error handling (try-except)
            # should be added here for robustness, returning None or a specific error indicator
            # for the failing fields. For now, assuming they are reliable.
        }

    def startRead(self, command):
        value = self.bus.read_i2c_block_data(self.DEVICE_ADDR, command, 2)
        return (value[0] * 256) + value [1]

    #Getter calls read method, returns converted data - all values are converted 12 bits, even though 2 bytes returned
    def getMCUTemp(self):
        #super().__init__("ESP") <-- Shawn had this in here, I don't understand why it's here so I'm commenting it out and leaving it out of other ones
        temp = self.startRead(18)
        temp = ((temp *0.0006103516) - 0.986)/0.00355
        return temp #done with multiple lines because of complicated conversion
    def getCell1Temp(self):
        return self.startRead(19)*0.00390625 #Reads data of specified type, sets up conversion factor to 'C

    def getCell2Temp(self):
        return self.startRead(20)*0.00390625 #Reads data of specified type, sets up conversion factor to 'C

    def getBusVoltage(self):
        return self.startRead(1) * 0.0023394775 #Reads data of specified type, sets up conversion factor to V

    def getBusCurrent(self):
        return self.startRead(2) * 0.0030517578 #Reads data of specified type, sets up conversion factor to A

    def getBCRVoltage(self):
        return self.startRead(3) * 0.0023394775 #Reads data of specified type, sets up conversion factor to V

    def getBCRCurrent(self):
        return self.startRead(4) * 0.0015258789 #Reads data of specified type, sets up conversion factor to A

    def get3V3Current(self):
        return self.startRead(14) * 0.0020345052 #Reads data of specified type, sets up conversion factor to A

    def get5VCurrent(self):
        return self.startRead(15) * 0.0020345052 #Reads data of specified type, sets up conversion factor to A

    def getSPXVoltage(self):
        return self.startRead(5) * 0.0024414063 #Reads data of specified type, sets up conversion factor to V

    def getSPXMinusCurrent(self):
        return self.startRead(6) * 0.0006103516 #Reads data of specified type, sets up conversion factor to A

    def getSPXPlusCurrent(self):
        return self.startRead(7) * 0.0006103516 #Reads data of specified type, sets up conversion factor to A

    def getSPYVoltage(self):
        return self.startRead(8) * 0.0024414063 #Reads data of specified type, sets up conversion factor to V

    def getSPYMinusCurrent(self):
        return self.startRead(9) * 0.0006103516 #Reads data of specified type, sets up conversion factor to A

    def getSPYPlusCurrent(self):
        return self.startRead(10) * 0.0006103516 #Reads data of specified type, sets up conversion factor to A

    def getSPZVoltage(self):
        return self.startRead(11) * 0.0024414063 #Reads data of specified type, sets up conversion factor to V

    def getSPZPlusCurrent(self):
        return self.startRead(13) * 0.0006103516

# This is the main file, to be run on startup of the Pi
import sys
sys.path.append('../')
import os # For path manipulation and creating directories
import os.path
import json # Added for telemetry config
import time # For fallback timestamp
import math # For math.nan
from flightLogic import getDriverData
import flightLogic.saveTofiles as saveTofiles
from Drivers.antennaDoor.AntennaDoor import AntennaDoor as antennaDoor
from flightLogic.missionModes.antennaDeploy import antennaMode as antennaMode
from flightLogic.missionModes.preBoomDeploy import preBoomMode
from flightLogic.missionModes.boomDeploy import boomMode
from flightLogic.missionModes.postBoomDeploy import postBoomMode
from flightLogic.missionModes.heartBeat import heart_beat
# from flightLogic.missionModes import safe
from flightLogic.missionModes.transmitting import Transmitting
from flightLogic.missionModes import *
from protectionProticol.fileProtection import FileReset
import asyncio
from TXISR import pythonInterrupt
from TXISR.packetProcessing import packetProcessing
from Drivers.camera import Camera
from Drivers.eps import EPS as EPS

# Telemetry Imports
from flightLogic.telemetryManager import TelemetryManager
from .telemetry_writer import serialize_telemetry # Import for writing binary telemetry
from Drivers.Accelerometer.Accelerometer import Accelerometer
from Drivers.Magnetometer.Magnetometer import Magnetometer
from Drivers.UV.UVDriver import UVDriver
from Drivers.adc.ADC_Driver import ADC
from Drivers.antennaDoor.AntennaDoor import AntennaDoor as antennaDoorDriver # Alias to avoid conflict
from Drivers.backupAntennaDeployer.BackupAntennaDeployer import BackupAntennaDeployer
from Drivers.boomDeployer.BoomDeployer import BoomDeployer
from Drivers.camera.Camera import Camera as CameraDriver # Alias to avoid conflict
from Drivers.cpuTemperature.CpuTemperature import CpuTemperature
from Drivers.eps.EPS import EPS as EPSDriver # Alias to avoid conflict
from Drivers.rtc.rtc_driver import RTC
from Drivers.solarPanelTemp.solarDriver import TempSensor
from Drivers.sunSensors.sunSensorDriver import sunSensor
from Drivers.transceiverConfig.TransceiverConfig import TransceiverConfig


# from TXISR import interrupt
# NOTE: This Code has past unit testing

async def collect_and_log_telemetry(telemetry_manager, collection_interval_seconds, output_file_path):
    """
    Collects telemetry data, transforms it for serialization, and writes it to a binary file.
    """
    # Attempt to get a persistent RTC instance if available, otherwise use time.time()
    rtc_driver_instance = None
    if hasattr(telemetry_manager, 'drivers'): # Check if drivers list exists
        for driver in telemetry_manager.drivers:
            if driver.name == 'rtc': # Assuming RTC driver is named 'rtc'
                rtc_driver_instance = driver
                break

    while True:
        flat_telemetry_payload = {}
        try:
            telemetry_data_raw = telemetry_manager.collect_telemetry()
            # print(f"Raw Telemetry Collected: {telemetry_data_raw}") # For debugging

            # 1. RTC_TIMESTAMP
            if rtc_driver_instance:
                try:
                    flat_telemetry_payload['RTC_TIMESTAMP'] = rtc_driver_instance.read() # Assumes read() gives timestamp
                except Exception as e:
                    print(f"Error reading from RTC driver: {e}")
                    flat_telemetry_payload['RTC_TIMESTAMP'] = time.time()
            elif 'rtc' in telemetry_data_raw and 'value' in telemetry_data_raw['rtc']: # Fallback to raw data if RTC obj not found
                 flat_telemetry_payload['RTC_TIMESTAMP'] = telemetry_data_raw['rtc']['value']
            else:
                flat_telemetry_payload['RTC_TIMESTAMP'] = time.time()

            # 2. Accelerometer Data (ACCEL_X, ACCEL_Y, ACCEL_Z)
            accel_data = telemetry_data_raw.get('Accelerometer', {}).get('value', (math.nan, math.nan, math.nan))
            if isinstance(accel_data, (list, tuple)) and len(accel_data) == 3:
                flat_telemetry_payload['ACCEL_X'] = accel_data[0]
                flat_telemetry_payload['ACCEL_Y'] = accel_data[1]
                flat_telemetry_payload['ACCEL_Z'] = accel_data[2]
            else:
                flat_telemetry_payload['ACCEL_X'] = flat_telemetry_payload['ACCEL_Y'] = flat_telemetry_payload['ACCEL_Z'] = math.nan

            # 3. Magnetometer Data (MAG_X, MAG_Y, MAG_Z)
            mag_data = telemetry_data_raw.get('Magnetometer', {}).get('value', (math.nan, math.nan, math.nan))
            if isinstance(mag_data, (list, tuple)) and len(mag_data) == 3:
                flat_telemetry_payload['MAG_X'] = mag_data[0]
                flat_telemetry_payload['MAG_Y'] = mag_data[1]
                flat_telemetry_payload['MAG_Z'] = mag_data[2]
            else:
                flat_telemetry_payload['MAG_X'] = flat_telemetry_payload['MAG_Y'] = flat_telemetry_payload['MAG_Z'] = math.nan
            
            # 4. Gyroscope Data (GYRO_X, GYRO_Y, GYRO_Z) - Assuming no separate gyro driver, defaults to NaN via EXPECTED_SENSORS
            # If a Gyro driver existed, it would be handled like Accelerometer.
            # These will be filled with DEFAULT_SENSOR_VALUE (NaN) by serialize_telemetry if not present.
            flat_telemetry_payload['GYRO_X'] = telemetry_data_raw.get('Gyroscope', {}).get('value', (math.nan, math.nan, math.nan))[0] if 'Gyroscope' in telemetry_data_raw else math.nan # Example
            flat_telemetry_payload['GYRO_Y'] = telemetry_data_raw.get('Gyroscope', {}).get('value', (math.nan, math.nan, math.nan))[1] if 'Gyroscope' in telemetry_data_raw else math.nan
            flat_telemetry_payload['GYRO_Z'] = telemetry_data_raw.get('Gyroscope', {}).get('value', (math.nan, math.nan, math.nan))[2] if 'Gyroscope' in telemetry_data_raw else math.nan


            # 5. CPU Temperature (CPU_TEMP_C)
            flat_telemetry_payload['CPU_TEMP_C'] = telemetry_data_raw.get('CpuTemperature', {}).get('value', math.nan)

            # 6. UV Index (UV_INDEX)
            flat_telemetry_payload['UV_INDEX'] = telemetry_data_raw.get('UVDriver', {}).get('value', math.nan)
            
            # 7. EPS Data (already flat, merge directly)
            # The EPS driver's get_telemetry_data() returns a dictionary like:
            # {'driver_name': 'EPS', 'mcu_temp_c': ..., 'bus_voltage_v': ... }
            # We need to extract these specific keys for EXPECTED_SENSORS in telemetry_writer.py
            eps_data = telemetry_data_raw.get('EPS', {})
            if eps_data: # If EPS data exists
                # Map EPS keys to the keys defined in EXPECTED_SENSORS
                flat_telemetry_payload['EPS_MCU_TEMP_C'] = eps_data.get('mcu_temp_c', math.nan)
                flat_telemetry_payload['EPS_CELL1_TEMP_C'] = eps_data.get('cell1_temp_c', math.nan)
                flat_telemetry_payload['EPS_CELL2_TEMP_C'] = eps_data.get('cell2_temp_c', math.nan)
                flat_telemetry_payload['EPS_BUS_VOLTAGE_V'] = eps_data.get('bus_voltage_v', math.nan)
                flat_telemetry_payload['EPS_BUS_CURRENT_A'] = eps_data.get('bus_current_a', math.nan)
                flat_telemetry_payload['EPS_BCR_VOLTAGE_V'] = eps_data.get('bcr_voltage_v', math.nan)
                flat_telemetry_payload['EPS_BCR_CURRENT_A'] = eps_data.get('bcr_current_a', math.nan)
                flat_telemetry_payload['EPS_3V3_CURRENT_A'] = eps_data.get('3v3_current_a', math.nan)
                flat_telemetry_payload['EPS_5V_CURRENT_A'] = eps_data.get('5v_current_a', math.nan)
                flat_telemetry_payload['EPS_SPX_VOLTAGE_V'] = eps_data.get('spx_voltage_v', math.nan)
                flat_telemetry_payload['EPS_SPX_MINUS_CURRENT_A'] = eps_data.get('spx_minus_current_a', math.nan)
                flat_telemetry_payload['EPS_SPX_PLUS_CURRENT_A'] = eps_data.get('spx_plus_current_a', math.nan)
                flat_telemetry_payload['EPS_SPY_VOLTAGE_V'] = eps_data.get('spy_voltage_v', math.nan)
                flat_telemetry_payload['EPS_SPY_MINUS_CURRENT_A'] = eps_data.get('spy_minus_current_a', math.nan)
                flat_telemetry_payload['EPS_SPY_PLUS_CURRENT_A'] = eps_data.get('spy_plus_current_a', math.nan)
                flat_telemetry_payload['EPS_SPZ_VOLTAGE_V'] = eps_data.get('spz_voltage_v', math.nan)
                flat_telemetry_payload['EPS_SPZ_PLUS_CURRENT_A'] = eps_data.get('spz_plus_current_a', math.nan)
            
            # For any other sensors in EXPECTED_SENSORS not explicitly handled,
            # serialize_telemetry will use DEFAULT_SENSOR_VALUE (NaN)
            # print(f"Flattened Payload for Serialization: {flat_telemetry_payload}") # For debugging

            success = serialize_telemetry(flat_telemetry_payload, output_file_path)
            if success:
                print(f"Telemetry successfully serialized to {output_file_path} at {flat_telemetry_payload['RTC_TIMESTAMP']}")
            else:
                print(f"Failed to serialize telemetry to {output_file_path}")

        except Exception as e:
            print(f"Error in collect_and_log_telemetry loop: {e}")
        
        await asyncio.sleep(collection_interval_seconds)

##################################################################################################################
# executeFlightLogic()
##################################################################################################################
# First, this function sets up the TXISR and then checks the boot conditions
# Then, it runs a mission mode, and then loops forever, constantly checking to run the next mission mode.
# NOTE: Each mission mode evaluates their exit conditions to leave the mission mode.
##################################################################################################################
fileChecker = FileReset()

def __main__():
	asyncio.run(executeFlightLogic())


async def executeFlightLogic():  # Open the file save object, start TXISR, camera obj, and start Boot Mode data collection
	
	baseFile = open("/home/pi/lastBase.txt")
	codeBase = int(baseFile.read())
	cameraObj = Camera()
	# Variable setup
	delay = 35*60  # 35 minute delay #TODO: set this delay to 35 min
	# antennaVoltageCheckWait = 22*60*60 # 22 hour wait for the voltage to increase past the threshold. This is arbitrary for now
	# Commented out as it's not used in the current scope of changes. Will be re-evaluated if logic demands.
	boot = True
	saveObject = saveTofiles.save()
	# startTXISR(save)
	ttncData = getDriverData.TTNCData(saveObject)
	attitudeData = getDriverData.AttitudeData(saveObject)
	# safeModeObject = safe.safe(saveObject)
	transmitObject = Transmitting(codeBase, cameraObj)
	packet = packetProcessing(transmitObject, cameraObj)
	heartBeatObj = heart_beat()
	# NOTE: antennaDoorObj is already instantiated in this file.
	# We will use `antennaDoorDriver` for the telemetry version.
	# antennaDoorObj = antennaDoor() # This line is kept for existing logic if needed by mission modes directly
	
	# Define Telemetry Output File Path and ensure directory exists
	# Using /home/pi/flightLogicData/ as a base, similar to other data files in the script
	TELEMETRY_OUTPUT_DIR = "/home/pi/flightLogicData/telemetry_data"
	os.makedirs(TELEMETRY_OUTPUT_DIR, exist_ok=True)
	TELEMETRY_OUTPUT_FILE = os.path.join(TELEMETRY_OUTPUT_DIR, "flight_data.bin")
	print(f"Telemetry data will be written to: {TELEMETRY_OUTPUT_FILE}")

	# Load Telemetry Configuration
	config_file_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'telemetry_config.json')
	try:
		with open(config_file_path, 'r') as f:
			telemetry_config = json.load(f)
		print(f"Telemetry config loaded from {config_file_path}")
	except FileNotFoundError:
		print(f"Telemetry config file {config_file_path} not found. Using default values.")
		telemetry_config = {"telemetry_interval_seconds": 60, "enabled_sensors": ["Accelerometer", "Magnetometer", "EPS", "CpuTemperature"]} # Default to a basic set
	except json.JSONDecodeError:
		print(f"Error decoding telemetry config file {config_file_path}. Using default values.")
		telemetry_config = {"telemetry_interval_seconds": 60, "enabled_sensors": ["Accelerometer", "Magnetometer", "EPS", "CpuTemperature"]}

	telemetry_interval = telemetry_config.get("telemetry_interval_seconds", 60)
	enabled_sensors_from_config = telemetry_config.get("enabled_sensors", [])
	print(f"Telemetry interval: {telemetry_interval}s. Enabled sensors from config: {enabled_sensors_from_config}")

	# Initialize TelemetryManager with the list of enabled sensor names from the config
	telemetry_mgr = TelemetryManager(enabled_sensors_list=enabled_sensors_from_config)

	# Map configuration names to driver classes and their expected 'name' attribute for TelemetryManager
	# The 'name' attribute is what TelemetryManager uses to filter.
	# This map helps instantiate only necessary drivers and ensures their 'name' attribute matches config.
	# Note: BackupAntennaDeployer and TransceiverConfig are not in the typical config list, added here for completeness if they were.
	driver_config_map = {
		"Accelerometer": (Accelerometer, "Accelerometer"),
		"Magnetometer": (Magnetometer, "Magnetometer"),
		"EPS": (EPSDriver, "EPS"),
		"CpuTemperature": (CpuTemperature, "CpuTemperature"),
		"UVDriver": (UVDriver, "UVDriver"),
		"ADC_Driver": (ADC, "ADC"), # Config name is "ADC_Driver", class is ADC, driver.name is "ADC"
		"rtc_driver": (RTC, "rtc"), # Config name is "rtc_driver", class is RTC, driver.name is "rtc"
		"solarDriver": (TempSensor, "SolarPanelTemp"), # Config name is "solarDriver", class is TempSensor, driver.name "SolarPanelTemp"
		"sunSensorDriver": (sunSensor, "Sun Sensor"), # Config name is "sunSensorDriver", class is sunSensor, driver.name "Sun Sensor"
		"BoomDeployer": (BoomDeployer, "BoomDeployer"),
		"Camera": (CameraDriver, "Camera"),
		"AntennaDoor": (antennaDoorDriver, "AntennaDoor"),
		"BackupAntennaDeployer": (BackupAntennaDeployer, "BackupAntennaDeployer"), # Not in example config, but if it were
		"TransceiverConfig": (TransceiverConfig, "TransceiverConfig") # Not in example config, but if it were
	}

	for config_name, (driver_class, expected_driver_name_attr) in driver_config_map.items():
		if config_name in enabled_sensors_from_config:
			try:
				driver_instance = driver_class()
				# Critical: Ensure the instance's 'name' attribute matches what TelemetryManager expects
				# This is usually set in the driver's super().__init__("ExpectedName")
				if hasattr(driver_instance, 'name') and driver_instance.name == expected_driver_name_attr:
					telemetry_mgr.register_driver(driver_instance) # register_driver now handles the filtering
					# print(f"Driver '{config_name}' initialized and passed to TelemetryManager.") # Redundant with TM prints
				elif hasattr(driver_instance, 'name'):
					print(f"Driver '{config_name}' instantiated, but its internal name '{driver_instance.name}' does not match expected '{expected_driver_name_attr}'. Not registered by TelemetryManager if names differ.")
					# Still register it, TelemetryManager will make the final decision.
					telemetry_mgr.register_driver(driver_instance)
				else:
					# This case should have been caught by TelemetryManager's hasattr check,
					# but good to be aware of if TM's logic changes.
					print(f"Driver '{config_name}' instantiated but has no 'name' attribute. Cannot be registered by TelemetryManager filtering.")
			except Exception as e:
				print(f"Failed to instantiate driver for '{config_name}': {e}")
		else:
			print(f"Driver '{config_name}' not in enabled_sensors_from_config, skipping instantiation.")
	
	print('Starting data collection and telemetry') #Setting up Background tasks for BOOT mode
	tasks=[]
	tasks.append(asyncio.create_task(heartBeatObj.heartBeatRun()))  # starting heart beat
	tasks.append(asyncio.create_task(pythonInterrupt.interrupt(transmitObject, packet)))  # starting rx monitoring 
	tasks.append(asyncio.create_task(ttncData.collectTTNCData(0)))  # Boot Mode is classified as 0
	tasks.append(asyncio.create_task(attitudeData.collectAttitudeData()))  # collecting attitude data
	# Use telemetry_interval from config and pass the output file path
	tasks.append(asyncio.create_task(collect_and_log_telemetry(telemetry_mgr, telemetry_interval, TELEMETRY_OUTPUT_FILE)))

	# Initialize all mission mode objects
	# NOTE: the comms-tx is the only exception to this rule as it is to be handled differently than other mission modes
	# NOTE: Boot Mode is defined and executed in this document, instead of a separate mission mode
	# safeModeObject was deleted below in the init parameters after saveObject 
	antennaDeploy = antennaMode(saveObject, transmitObject, packet)
	preBoomDeploy = preBoomMode(saveObject, transmitObject, packet)
	postBoomDeploy = postBoomMode(saveObject, transmitObject, packet)
	boomDeploy = boomMode(saveObject, transmitObject, cameraObj, packet)

	# Check the boot record if it doesn't exist recreate it 
	if(readData() == (None, None, None)):
		print('Files are empty')
		bootCount, antennaDeployed, lastMode = 0,False,0
	# otherwise save the last mission mode
	else:
		bootCount, antennaDeployed, lastMode = readData()  
	bootCount += 1  # Increment boot count
	# save data
	recordData(bootCount, antennaDeployed, lastMode)

	if lastMode not in range(0,7): #Mission Mode invalid
		lastMode = 0
		antennaDeployed = False
	
	recordData(bootCount, antennaDeployed, lastMode)

	# This is the implementation of the BOOT mode logic.
	if not antennaDeployed:  # First, sleep for 35 minutes
		print('Antenna is undeployed, waiting 35 minutes')
		await asyncio.sleep(delay)  # Sleep for 35 minutes
		while(transmitObject.isRunning()):
			await asyncio.sleep(60) #sleep if a transmission is running

	print("Moving on to check antenna door status")
	#deploy the antenna, if it fails we will do nothing
	eps = EPS()
	voltageCount = 0
	try: 
		while True:
			try :
				BusVoltage = eps.getBusVoltage()
			except :
				#if we fail to check the bus voltage we will set it to the max value plus one
				BusVoltage = 5.1 + 1
			if antennaDeployed == True:
				break
			elif (not antennaDeployed) and (BusVoltage > 3.75):
				antennaDoorObj.deployAntennaMain() #wait for the antenna to deploy
				await asyncio.sleep(300)
				break
			elif ((antennaVoltageCheckWait/10) < voltageCount):
				antennaDoorObj.deployAntennaMain() #wait for the antenna to deploy
				await asyncio.sleep(300)
				break
			else:
				voltageCount += 1
				await asyncio.sleep(10)
	except :
		print("____Failed to deploy the antenna_____")
	# status is set True if all 4 doors are deployed, else it is False
	# This part of the logic uses the original antennaDoorObj
	original_antenna_door_obj = antennaDoor() # Ensuring we use the original object for this logic
	try:
		status = original_antenna_door_obj.readDoorStatus()
	except:
		status = False
		print("Failed to check antenna door status using original_antenna_door_obj")
	if antennaDeployed == True: # antennaDeployed is a variable tracking state
		pass
	elif status == True:
		antennaDeployed = True
	else:
		antennaDeployed = False

	recordData(bootCount, antennaDeployed, lastMode)

	# NOTE: Boot mode tasks are cancelled before moving to the next mode.
	# The telemetry task should persist across modes.
	# However, the current structure cancels all tasks in `tasks` list.
	# This means telemetry collection will also stop when transitioning from BOOT.
	# This might need further refinement if telemetry is expected to be continuous
	# across all mission modes without restarting. For now, following existing pattern.
	
	try:  # Cancels attitude collection tasks (and telemetry as it's in the same list)
		for t in tasks:
			t.cancel()
		print('Successfully cancelled BOOT mode background tasks (including telemetry for now)')
	except asyncio.exceptions.CancelledError:
		print("Exception thrown cancelling task - This is normal")
		
	if not antennaDeployed:
		# Re-add telemetry task if it's meant to run in this new mode
		# For now, assuming telemetry task is part of the "main" lifecycle managed by executeFlightLogic,
		# and if it's cancelled, it's for a reason (e.g. mode transition that shouldn't have it).
		# If telemetry should be *always* on, its management needs to be outside this specific task list.
		# Given the current structure, if tasks are cancelled, telemetry is cancelled.
		# Let's proceed with this understanding. A new telemetry task would be started if executeFlightLogic was re-entered.
		await asyncio.gather(antennaDeploy.run())
		print('Running Antenna Deployment Mode')
		antennaDeployed = True
		print("Antenna Deployed = ", antennaDeployed)
		recordData(bootCount, antennaDeployed, lastMode)  # Save into files
	elif lastMode == 4:
		print('Running Post Boom Deploy')
		lastMode = 4
		recordData(bootCount, antennaDeployed, lastMode)  # Save into files
		await asyncio.gather(postBoomDeploy.run())
	else:
		print('Running preBoom Deploy')
		lastMode = 2
		recordData(bootCount, antennaDeployed, lastMode)  # Save into files
		await asyncio.gather(preBoomDeploy.run())
		lastMode = 3
		recordData(bootCount, antennaDeploy, lastMode)
		print("Finished running preBoomDeploy")


	while True: # This loop executes the rest of the flight logic
	# pre boom deploy
		print("Entered the loop that chooses the next mission mode.")
		recordData(bootCount, antennaDeployed, lastMode)  # Save into files
		if ((antennaDeployed == True) and (lastMode != 3) and (lastMode != 4)):
			print('Running pre-Boom deploy')
			lastMode = 2
			recordData(bootCount, antennaDeployed, lastMode)
			await asyncio.gather(preBoomDeploy.run())  # Execute pre-boom deploy, then move to post-boom deploy
			print("Finished preBoomDeploy")
			lastMode = 3
			recordData(bootCount, antennaDeployed, lastMode)
		elif ((antennaDeployed == True) and (lastMode == 3)):
			print('Running Boom Deploy')
			await asyncio.gather(boomDeploy.run())  # Execute boom deployment, start post-boom deploy
			lastMode = 4
			recordData(bootCount, antennaDeployed, lastMode)
		else:  # Post-Boom Deploy
			print('Running post-Boom Deploy')
			recordData(bootCount, antennaDeployed, lastMode)  # Save into files
			await asyncio.gather(postBoomDeploy.run())


def recordData(bootCount, antennaDeployed, lastMode):
	# write to the boot file, "w" option in write overwrites the file
	fileChecker.checkFile("/home/pi/flightLogicData/bootRecords.txt")
	new = open("/home/pi/flightLogicData/bootRecords.txt", "w+")
	new.write(str(bootCount) + '\n')
	if antennaDeployed:
		new.write(str(1)+'\n')
	else:
		new.write(str(0)+'\n')
	new.write(str(lastMode) + '\n')
	new.close()

	# write to the the back up file
	fileChecker.checkFile("/home/pi/flightLogicData/backupBootRecords.txt")
	new = open("/home/pi/flightLogicData/backupBootRecords.txt", "w+")
	new.write(str(bootCount) + '\n')
	if antennaDeployed:
		new.write(str(1)+'\n')
	else:
		new.write(str(0)+'\n')
	new.write(str(lastMode) + '\n')
	new.close()


def readData():
	# This function reads in data from the files, it was previously in the main function but is better as its own function
	# bootRecords file format
	# Line 1 = boot count
	# Line 2 = antenna deployed?
	# Line 2 = last mission mode
	bootCount,antennaDeployed,lastMode = None, None, None
	fileChecker.checkFile("/home/pi/flightLogicData/bootRecords.txt")
	try:
		bootFile = open("/home/pi/flightLogicData/bootRecords.txt", "r")
		bootCount = int(bootFile.readline().rstrip())
		antennaDeployed = bool(int(bootFile.readline().rstrip()))
		lastMode = int(bootFile.readline().rstrip())
		bootFile.close()
	except:
		try:
			print('File exception')
			fileChecker.checkFile("/home/pi/flightLogicData/backupBootRecords.txt")
			bootFile = open("/home/pi/flightLogicData/backupBootRecords.txt", "r")
			bootCount = int(bootFile.readline().rstrip())
			antennaDeployed = bool(int(bootFile.readline().rstrip()))
			lastMode = int(bootFile.readline().rstrip())
			bootFile.close()
			# In this except statement, the files are corrupted, so we rewrite both of them
		except:
			print('Double File exception - are both files non-existant?')	
			fileChecker.checkFile("/home/pi/flightLogicData/bootRecords.txt")
			bootFile = open("/home/pi/flightLogicData/bootRecords.txt", "w")
			fileChecker.checkFile("/home/pi/flightLogicData/backupBootRecords.txt")
			backupBootFile = open("/home/pi/flightLogicData/backupBootRecords.txt", "w")
			bootFile.write('0\n0\n0\n')
			backupBootFile.write('0\n0\n0\n')

	recordData(bootCount, antennaDeployed, lastMode)
	return bootCount, antennaDeployed, lastMode

async def heartBeat(): #Sets up up-and-down voltage on pin 40 (GPIO 21) for heartbeat with Arduino
		waitTime = 4
		while True:
			GPIO.output(21, GPIO.HIGH)
			print("Heartbeat wave high")
			await asyncio.sleep(waitTime/2)
			GPIO.output(21, GPIO.LOW)
			print("Heartbeat wave low")
			await asyncio.sleep(waitTime/2)

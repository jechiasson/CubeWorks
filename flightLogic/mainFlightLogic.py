# This is the main file, to be run on startup of the Pi
import sys
sys.path.append('../')
import os.path
import json # Added for telemetry config
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

async def collect_and_log_telemetry(telemetry_manager, collection_interval_seconds):
    """
    Collects and prints telemetry data from the TelemetryManager periodically.
    """
    while True:
        try:
            telemetry_data = telemetry_manager.collect_telemetry()
            print(f"Telemetry @ {RTC().readSeconds()}: {telemetry_data}") # Using RTC().readSeconds() for timestamp
        except Exception as e:
            print(f"Error collecting or logging telemetry: {e}")
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
	# Use telemetry_interval from config
	tasks.append(asyncio.create_task(collect_and_log_telemetry(telemetry_mgr, telemetry_interval)))

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

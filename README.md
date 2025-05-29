# CubeWorks
Flight software for the GASPACS mission written in Python, with some compents in c. 

## Introduction
The Get Away Special Passive Attitude Control Satellite (GASPACS) is an experimental 1U cubesat in development by Utah State University's Get Away Special team.  The purpose of the experiment is to test the viability of an inflatable aero-stabilization boom deployable component in Low Earth Orbit (LEO).  This repository contains CubeWorks, the flight software for the satellite. The CubeWorks software module is designed to run on a Raspberry Pi Zero W running Raspbian lite os as its operating system.


## Objectives
CubeWorks is intended to be a robust, modular, and fault tolerant software framework for small satellites, with minimal barrier to entry.  The experienced developer may be asking, "Why write the entire framework in python and not a more performant language with closer hardware interaction?"  The answer is because the framework is designed to be accessible to newer developers who want to get into space research.  The software isn't as performant as an equivalent solution written in, say, c++ but it isn't designed to be.   

Framework components are designed to be modular, and easy to add to and remove from a given system.  All that is needed is to define a driver that interacts with your hardware components and inherits from the built in `Component` class, and include it in the main file.  

## Installation

### PREFERRED Installation Process with CubeWorks Image 
1. Download the [CubeWorks Raspbian Lite image V6](https://drive.google.com/file/d/1ozvCZwbu9eHb0bZ5SgTERq1yh5yXUiuP/view)
2. Flash image onto 8GB micro SD card
3. Run image on Raspberry Pi Zero W
4. Log in (username: pi		password: spaceorbust2021)
5. IMPORTANT: Make sure to enable the Serial port via raspi-config. Also update the chronodot time (see Software Unit Testing Procedure document for instructions)
6. Run `./install.exe`
7. Use `htop` and check to see in main flight logic is running

### INSTALLING SSDV
1. `git clone https://github.com/SmallSatGasTeam/ssdv`
2. `cd ssdv`
3. `make`
4. `nano ~/.bashrc`
5. Add the following line to the bashrc file:
	`export PATH=$PATH:/home/pi/ssdv/ssdv`
6. Reboot the pi, and make sure you can run `ssdv` from any spot on the pi

### INSTALLING SSDV
1. `git clone https://github.com/SmallSatGasTeam/ssdv`
2. `cd ssdv`
3. `make`
4. `nano ~/.bashrc`
5. Add the following line to the bashrc file:
	`export PATH=$PATH:/home/pi/ssdv`
6. Reboot the pi, and make sure you can run `ssdv` from any spot on the pi

### MANUAL Installation Process (How the CubeWorks Image was created)
1. Image a Raspberry Pi with Raspbian lite and boot the Pi
2. Use `sudo raspi-config` to set the proper network settings, set a user password, localisation options.
3. Under Interfacing Options enable Camera, SSH, SPI, I2C, and Serial ("No" to login shell, "Yes" to serial interface)
3. Update all packages with the commands: `sudo apt update` `sudo apt full-upgrade`
4. Reboot, install the following dependencies:
	- Python3, `sudo apt install python3`
	- python3-pip, `sudo apt install python3-pip`
	- NumPy, `sudo apt install python3-numpy`
5. Create the exe file to run for the installation process, run "gcc install.c -o install.exe"
6. run "./install.exe"
7. To run the testMainFlightLogic.py file (or any other program) on startup, run `sudo crontab -e` and then add the following line to the end of the file:
`@reboot sudo runuser pi -c "cd ; ./startup.exe"`.  

### File Structure
This file structure comprises the major compoments of CubeWorks.  

### Up dating the code:
1. Get the updateCode.c (it should be in any of the cubeworks repositories.)
2. use this command `gcc upDateCode.c -o upDateCode.exe ; cp upDateCode.exe ~/ ; rm upDateCode.exe`
3. return to the root and then use `./upDateCode.exe`

### Important Notes:
-TX windows have to be seperated by at least 25 seconds. This is the time from ending one window to the start time of the next window. If it is not separated by this buffer, then it is NOT guaranted that the TX window will be serviced. 

### Setting up chronodot
1. Ensure chronodot is connected to the pi and is powered on.
2. Edit the file `/etc/modules` and add `rtc-ds1307` to the bottom
3. Reboot the pi
4. Edit the file `/etc/rc.local` and add the following lines before the `exit 0` line:
	- `echo ds1307 0x68 > /sys/class/i2c-adapter/i2c-1/new_device
	hwclock -s`
5. The end of the file should look like:
	- `echo ds1307 0x68 > /sys/class/i2c-adapter/i2c-1/new_device
	hwclock -s
	exit0`
6. Reboot the pi

### Setting the time on the chronodot
1. Set the time with the command `sudo date -s "29 AUG 2010 13:00:00"` 
2. Update the chronodot time with the command `sudo hwclock -w`
3. Note: The pi reads the time from the chronodot on boot and sets its internal clock to match that time. If you change the pi time, you have to update the chronodot as well or the updated time will be lost on a boot cycle.


### setting up the Cammera 

1.use `sudo raspi-config` 

2.go to go to the `interface` tab 

3.Enable cammera in settings

## seting up the serial interface
1.use `sudo raspi-config`

2.go to go to the `interface` tab

3.On the first tab select `no`

4.ON the second tab select `yes`




### Important Notes:
-TX windows have to be seperated by at least 25 seconds. This is the time from ending one window to the start time of the next window. If it is not separated by this buffer, then it is NOT guaranted that the TX window will be serviced. 


### To put the stack in flight configuration
-run the code called flightConfig.exe, `Warning: This will disable, wifi, hdmi, and the leds. You will have to reflash the sd if you want to commicate with the pi again.`

-If you want to still have wifi run flightConfigWifi.exe `Warning: This is for testing ONLY`
```
Pi system
├──Home
│   ├──CubeWorks0
│   ├──CubeWorks1
│   ├──CubeWorks2
│   ├──CubeWorks3
│   ├──CubeWorks4
│   ├──flightlogicData
│   |	├──Attitude_Data.txt
│   |	├──TTNC_Data.txt
│   |	├──BootRecords.txt
│   |	├──backupBootRecors.txt
│   |	└── Deploy_Data.txt
│   ├──TXISRData
│   |	├──AX25Flag.txt
│   |	├──flagsFile.txt
│   |	├──transmissionFla.txt
│   |	└── txWindows.txt
│   ├──install.exe
│   ├──lastBase.txt
└── └── upDateCode.exe


Cubeworks
├── Drivers
│   ├── ExampleDriver
│   │   ├── ExampleDriver.py
│   │   └── __init__.py
│   ├── __init__.py
│   └── Driver.py
├── flightLogic
│   ├── mainFlightLogic.py
│   ├── missionModes
│   │   └── example.py
│   ├── postBoomTime.txt
│   └── saveTofiles.py
├── GroundStation
│   ├── example.sh
│   └── example.py
├── __init__.py
├── log.txt
├── mission_modes.py
├── protectionProticol
│   └── fileProtection.py
├── README.md
├── requirements.txt
├── runOnBoot.py
├── tests
│   ├── __init__.py
│   ├── testAllDrivers.py
│   └── unit_testing_example.py
├── TXISR
│   ├── example.py
│   └── __init__.py
└── watchdog
    ├── arduino_watchdog_v7
    │   └── arduino_watchdog_v7.ino
    └── Heartbeat
        └── Heartbeat.py
```

### Class Structure

![class](https://user-images.githubusercontent.com/27446370/118514932-23915500-b6f2-11eb-9dde-4a1bd2eee4df.png)


###Data Flows:

[GAS software.pdf](https://github.com/SmallSatGasTeam/CubeWorks/files/6494865/GAS.software.pdf)

[Boom deploy data flow.pdf](https://github.com/SmallSatGasTeam/CubeWorks/files/6494888/Boom.deploy.data.flow.pdf)

[Data recived data flow.pdf](https://github.com/SmallSatGasTeam/CubeWorks/files/6494890/Data.recived.data.flow.pdf)

[Decode TX data flow.pdf](https://github.com/SmallSatGasTeam/CubeWorks/files/6494891/Decode.TX.data.flow.pdf)

[multi save data path.pdf](https://github.com/SmallSatGasTeam/CubeWorks/files/6494892/multi.save.data.path.pdf)

[multi save data path2.pdf](https://github.com/SmallSatGasTeam/CubeWorks/files/6494893/multi.save.data.path2.pdf)

[Post Boom deploy data flow.pdf](https://github.com/SmallSatGasTeam/CubeWorks/files/6494894/Post.Boom.deploy.data.flow.pdf)

[preboom deploy data flow.pdf](https://github.com/SmallSatGasTeam/CubeWorks/files/6494895/preboom.deploy.data.flow.pdf)

[prepare for tx data flow.pdf](https://github.com/SmallSatGasTeam/CubeWorks/files/6494896/prepare.for.tx.data.flow.pdf)

## COSMOS Telemetry Integration & Docker Setup

### Overview

This project now supports outputting telemetry data in a binary format that is compatible with OpenC3 COSMOS for command and control. The system is configured so that COSMOS ingests this telemetry data via a File Interface. The entire system, including the Python flight application and the COSMOS services, can be run locally using Docker Compose.

### Prerequisites

Before you begin, ensure you have the following installed:

*   **Docker:** [Installation Guide](https://docs.docker.com/get-docker/)
*   **Docker Compose:** [Installation Guide](https://docs.docker.com/compose/install/)
*   **(Optional) Access to OpenC3 COSMOS Docker images:** The `docker-compose.yaml` file is configured to pull COSMOS images. By default, it uses public images from `openc3/` on Docker Hub. If you are using a private registry or specific versions, you will need to adjust the environment variables in the `.env` file.

### Environment Variables

A `.env` file in the root directory is used to configure aspects of the Docker Compose setup, primarily for COSMOS image sources and credentials. Review and customize this file if needed. Key variables you might want to adjust include:

*   `OPENC3_REGISTRY`: The Docker registry for COSMOS images (default: `openc3`).
*   `OPENC3_NAMESPACE`: The namespace within the registry (often blank for public Docker Hub images).
*   `OPENC3_TAG`: The tag for COSMOS images (default: `latest`).
*   `OPENC3_USER_ID`: User ID for running COSMOS services (default: `1001`).
*   `OPENC3_GROUP_ID`: Group ID for running COSMOS services (default: `1001`).
*   Various passwords like `OPENC3_REDIS_PASSWORD`, `OPENC3_BUCKET_PASSWORD`, `OPENC3_SERVICE_PASSWORD`. The defaults are provided in the `.env` file; change them for a more secure setup if exposing services.

Review the `.env` file in the root of the repository and customize it for your environment, especially if you are using a private Docker registry or need to change default credentials.

### Running the System

To build and run the entire system:

```bash
docker-compose up --build
```

This command will:

1.  Build the Python application Docker image (`python-app`) based on the `Dockerfile`.
2.  Pull all necessary COSMOS Docker images from the configured registry (if they are not already present locally).
3.  Start all defined services (Python application, MinIO, Redis, COSMOS API, Operator, Traefik, etc.).

Once started:
*   The Python application (`python-app` service) will begin its flight logic, which includes generating telemetry data according to the `flightLogic/telemetry_config.json` and writing it to a binary file.
*   The COSMOS `openc3-operator` service will monitor this binary file for new telemetry packets.

### Telemetry Data Flow

The telemetry data flows from the Python application to COSMOS as follows:

1.  The Python application (running in the `python-app` Docker service) writes serialized binary telemetry data to `flight_data.bin` located in its `/telemetry_output` directory.
2.  This `/telemetry_output` directory within the `python-app` container is mapped to a Docker named volume called `telemetry_data_volume`.
3.  The COSMOS `openc3-operator` service also mounts this `telemetry_data_volume`. It is mapped to `/cosmos_tlm_input` inside the `openc3-operator` container.
4.  The `FileInterface` (named `FLIGHT_DATA_INT`) used by COSMOS is configured in `plugins/FLIGHT_SYSTEM_TARGET/config/plugin.txt`. This interface is set up to read telemetry files from the `/cosmos_tlm_input` directory.
5.  The structure of the telemetry packets that COSMOS expects to read is defined in `plugins/FLIGHT_SYSTEM_TARGET/config/cmd_tlm/telemetry.txt`. This definition must match the binary format produced by `flightLogic/telemetry_writer.py`.
6.  After processing, the `FileInterface` is configured to move the processed telemetry files to a directory, which is mapped to the `telemetry_archive_volume` (visible as `/cosmos_tlm_archive` inside the `openc3-operator` container).

### Accessing COSMOS

Once the Docker Compose setup is running, the COSMOS web interface should be accessible at:

*   **`http://localhost:2900`**

You can use COSMOS tools such as Telemetry Viewer, Packet Viewer, etc., to connect to the `FLIGHT_SYSTEM_TARGET` and view the `FLIGHT_PACKET` telemetry being received from the Python application.

### Stopping the System

To stop all running services and remove the containers:

```bash
docker-compose down
```

This command will stop and remove the containers. To also remove the named volumes (like `telemetry_data_volume`, `openc3_minio_data`, etc.), you can use `docker-compose down -v`.

### Telecommand Capabilities

#### Overview

The Python application can now be controlled via UDP commands sent from COSMOS. COSMOS is configured to send these commands via the `FLIGHT_CMD_UDP_INT` interface, targeting the `python-app` container on UDP port 9090.

#### Available Commands

The following commands are available:

*   **`ENABLE_TELEMETRY_CMD`**: Enables the transmission of telemetry packets.
*   **`DISABLE_TELEMETRY_CMD`**: Disables the transmission of telemetry packets.
*   **`RESTART_APP_CMD`**: Commands the Python application to shut down. If running under Docker with the `restart: unless-stopped` policy, the container will automatically restart.
*   **`SET_TELEMETRY_INTERVAL_CMD`**:
    *   Sets the interval for telemetry packet transmission.
    *   Parameter: `FREQUENCY_HZ` (Float). Example: `0.5` for a 2-second interval. A frequency of `0` or less will disable telemetry.

#### Sending Commands from COSMOS

Commands can be sent using the COSMOS 'Command Sender' tool:

1.  Select `FLIGHT_SYSTEM_TARGET` as the target.
2.  Choose the desired command from the command list (e.g., `ENABLE_TELEMETRY_CMD`, `SET_TELEMETRY_INTERVAL_CMD`).
3.  For `SET_TELEMETRY_INTERVAL_CMD`, fill in the `FREQUENCY_HZ` parameter before sending.

#### UDP Port

*   The Python application listens for commands on UDP port `9090` within the Docker network.
*   This port is mapped to `9090` on the host in the `docker-compose.yaml`.

# Use the official Python slim image as a parent image
FROM python:slim-latest

# Set the working directory in the container
WORKDIR /app

# Copy the entire current directory contents into the container at /app
# This includes flightLogic, Drivers, tests, config, plugins, etc.
COPY . .

# Check if requirements.txt exists and install any specified packages
# (The flightLogic and other local modules are made available by COPY .)
# This RUN instruction will only execute if requirements.txt is present in the build context
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Command to run the application
# Ensure mainFlightLogic.py is executable or called via python
# Assuming mainFlightLogic.py is in the flightLogic directory
CMD ["python", "flightLogic/mainFlightLogic.py"]

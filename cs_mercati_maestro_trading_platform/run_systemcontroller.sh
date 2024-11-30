#!/bin/bash

# Define the path to the Python script
SCRIPT_PATH="./SystemController.py"

# Check if the script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: $SCRIPT_PATH does not exist."
    exit 1
fi

# Launch the Python script
echo "Launching SystemController.py..."
python3 "$SCRIPT_PATH"

# Check if the script executed successfully
if [ $? -eq 0 ]; then
    echo "SystemController.py executed successfully."
else
    echo "SystemController.py encountered an error."
    exit 1
fi


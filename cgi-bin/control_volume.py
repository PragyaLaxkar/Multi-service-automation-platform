#!/usr/bin/python3

import subprocess
import cgi
# import cgitb
import json

# Enable debugging
# cgitb.enable()

def set_volume(volume_level):
    subprocess.run(["amixer", "sset", "Master", f"{volume_level}%"])

# Read input from the GET request
form = cgi.FieldStorage()
volume_value = form.getvalue("volume")

# Check if the volume value is provided and is a valid integer
if volume_value is None:
    response = {
        "status": "error",
        "message": "No volume level provided."
    }
elif not volume_value.isdigit() or not (0 <= int(volume_value) <= 100):
    response = {
        "status": "error",
        "message": "Invalid volume level. Please provide an integer between 0 and 100."
    }
else:
    volume_level = int(volume_value)
    set_volume(volume_level)
    response = {
        "status": "success",
        "volume": volume_level
    }

# Return a JSON response
print("Content-Type: application/json\n")
print(json.dumps(response))

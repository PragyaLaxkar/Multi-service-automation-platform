#!/usr/bin/python3

import cgi
import subprocess

print("Content-type: text/html")
print("")

# Get form data
form = cgi.FieldStorage()

# Extract WETTY_USER from form input
wetty_user = form.getvalue('wetty_user')

# Docker command to run
docker_command = [
    'sudo docker', 'run', '--name', 'term',
    '-e', f'WETTY_USER={wetty_user}',
    '-e', '$6$fdDYCEwV9PXWMOea$jTehUKNxzdVusLsbCzpHV3mmPqFoujJn8FMcTQQLQqI0NHV2CoMtlqPQvlrd8dkCRilLJ/hBwKIAPsx7PkAiC1',
    '-p', '3000:3000', '-dt', 'freeflyer/wetty'
]

# Run the Docker command
try:
    subprocess.run(docker_command, check=True)
    print(f"<html><body><h2>Docker container started successfully with WETTY_USER={wetty_user}</h2></body></html>")
except subprocess.CalledProcessError as e:
    print(f"<html><body><h2>Failed to start Docker container: {e}</h2></body></html>")


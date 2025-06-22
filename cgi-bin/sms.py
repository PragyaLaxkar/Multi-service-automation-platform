#!/usr/bin/env python3

import cgi
import cgitb
from twilio.rest import Client

# Enable CGI traceback for debugging
cgitb.enable()

# Print necessary headers
print("Content-Type: text/html\n")

# Create instance of FieldStorage
form = cgi.FieldStorage()

# Get data from fields
message_body = form.getvalue('message')

def send_sms_message(message_body):
    account_sid = ''
    auth_token = ''
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=message_body,
        from_='',
        to=''
    )
    return "SMS sent successfully."

if message_body:
    result = send_sms_message(message_body)
else:
    result = "No message body provided."

print(f"<html><body><h1>{result}</h1></body></html>")


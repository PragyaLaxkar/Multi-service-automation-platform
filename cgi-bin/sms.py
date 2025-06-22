#!/usr/bin/env python3

import cgi
import cgitb
import os
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
    # Get credentials from environment variables
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_FROM_NUMBER')
    to_number = os.environ.get('TWILIO_TO_NUMBER')
    
    # Check if environment variables are set
    if not all([account_sid, auth_token, from_number, to_number]):
        return "Error: Missing Twilio credentials in environment variables"
        
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=message_body,
        from_=from_number,
        to=to_number
    )
    return "SMS sent successfully."

if message_body:
    result = send_sms_message(message_body)
else:
    result = "No message body provided."

print(f"<html><body><h1>{result}</h1></body></html>")


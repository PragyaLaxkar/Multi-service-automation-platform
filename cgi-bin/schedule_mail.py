#!/usr/bin/env python3
import cgi
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

print('Content-Type: text/plain\n')

form = cgi.FieldStorage()

sender = form.getvalue('sender')
recipient = form.getvalue('recipient')
subject = form.getvalue('subject')
message = form.getvalue('message')

if not all([sender, recipient, subject, message]):
    print("Missing required fields.")
    exit()

# Email config
smtp_server = 'smtp.gmail.com'
smtp_port = 587
username = sender
password = ''  # Use app password

# Create message with attachment
msg = MIMEMultipart()
msg['From'] = sender
msg['To'] = recipient
msg['Subject'] = subject
msg.attach(MIMEText(message, 'plain'))

# Handle file upload
if "attachment" in form:
    file_item = form["attachment"]
    if file_item.filename:
        file_data = file_item.file.read()
        filename = os.path.basename(file_item.filename)

        part = MIMEApplication(file_data)
        part.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(part)

# Send the email
try:
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(username, password)
        server.send_message(msg)
    print("Email sent successfully.")
except Exception as e:
    print("Failed to send email:", str(e))

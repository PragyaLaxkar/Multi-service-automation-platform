#!/usr/bin/python3

import cgi
# import cgitb
from gtts import gTTS
import os
import shutil
import json

# cgitb.enable()

print("Content-Type: application/json\n")

# Get the text input from the user
form = cgi.FieldStorage()
text_to_speak = form.getvalue('text', '')

# Response dictionary
response = {}

if text_to_speak:
    try:
        # Generate speech
        tts = gTTS(text=text_to_speak, lang='en')
        
        # Save the file to /tmp directory
        tmp_audio_file = "/tmp/speech.mp3"
        tts.save(tmp_audio_file)
        
        # Move the file to /var/www/html/ and set permissions
        final_audio_file = "/var/www/html/speech.mp3"
        shutil.copy(tmp_audio_file, final_audio_file)
        os.chmod(final_audio_file, 0o644)
        
        # Send the URL to the audio file
        response = {
            'status': 'success',
            'audio_file': '/speech.mp3'
        }
    except Exception as e:
        response = {'status': 'error', 'message': str(e)}
else:
    response = {'status': 'error', 'message': 'No text provided'}

# Send JSON response
print(json.dumps(response))

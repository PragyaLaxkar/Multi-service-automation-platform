#!/usr/bin/env python3
import cgi
import cgitb
import json
import os
import google.generativeai as genai
import sys
import traceback

# sys.stderr = open('/tmp/cgi_error.log', 'a')

# Print HTTP headers
print("Content-Type: application/json\n")
form = cgi.FieldStorage()

# Enable CGI traceback for debugging
cgitb.enable()

# Configure Gemini API
GEMINI_API_KEY = ''  # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)

# Set up the model
model = genai.GenerativeModel('gemini-2.0-flash')

# Get form data
user_message = form.getvalue('message')

if user_message:
    try:
        # Generate response using Gemini API
        response = model.generate_content(user_message)
        bot_response = response.text

        # Return JSON response
        result = {"status": "success", "response": bot_response}
        print(json.dumps(result))
    except Exception as e:
        # Handle errors
        result = {"status": "error", "response": f"Error: {str(e)}"}
        print(json.dumps(result))
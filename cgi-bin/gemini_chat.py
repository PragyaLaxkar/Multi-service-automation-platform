#!/usr/bin/python3

import cgi
import os
import google.generativeai as genai
import sys
import traceback
import logging

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

print("Content-Type: text/plain\n")
form = cgi.FieldStorage()

# Configure the API key from environment variable
api_key = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=api_key)

# Define the generation configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Create the generative model
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
)

# Start a chat session
chat_session = model.start_chat(history=[])

# Parse form data
if "prompt" not in form:
    raise ValueError("Missing 'prompt' field in form submission.")

prompt = form.getvalue("prompt")

try:
    # Send the prompt to the model and get the response
    if prompt is None or str(prompt).strip() == "":
        print("Error: No input provided. Please enter a prompt.")
    else:
        response = chat_session.send_message(prompt)
        print(response.text)
except Exception as e:
    # Log the error to Apache error log
    print("Status: 500 Internal Server Error\n")
    print("Content-Type: text/plain\n")
    print(f"CGI Script Error: {e}")
    traceback.print_exc(file=sys.stderr)

#!/usr/bin/env python3

import cgi
import cgitb
import requests
import base64

cgitb.enable()


print("Content-Type: text/html\n")

form = cgi.FieldStorage()
prompt = form.getvalue('prompt')

if prompt:
    api_key = ""
    api_url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

    headers = {
        "authorization": f"Bearer {api_key}",
        "accept": "image/png",
        "content-type": "application/json"
    }

    data = {
        "text_prompts": [{"text": prompt}],
        "output_format": "jpeg",
        "steps": 30,
        "cfg_scale": 7.0,
        "width": 1024,
        "height": 1024
    }

    response = requests.post(api_url, headers=headers, json=data)

    if response.status_code == 200:
        img_data = base64.b64encode(response.content).decode('utf-8')
        print(f'<img src="data:image/jpeg;base64,{img_data}" alt="Generated Image">')
    else:
        print("<p>Error generating image: {}</p>".format(response.json()))
else:
    print("<p>Error: No prompt provided.</p>")
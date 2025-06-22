#!/usr/bin/python3
import sys
sys.path.append('/var/www/python_libs')
import cgitb
import json
import os
import logging

# Set up logging
logging.basicConfig(filename='/tmp/translate_text.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

print("Content-Type: application/json\n")

# Log sys.path to debug
logging.debug(f"sys.path: {sys.path}")

try:
    import googletrans
    logging.debug(f"googletrans version: {googletrans.__version__}")
    from googletrans import Translator, LANGUAGES
except ImportError as e:
    logging.error(f"Failed to import googletrans: {str(e)}")
    print(json.dumps({"status": "error", "message": f"Failed to import googletrans: {str(e)}"}))
    sys.exit(0)

response = {}

try:
    logging.debug("Script started")
    if os.environ.get('REQUEST_METHOD', '') == 'POST':
        content_length = int(os.environ.get('CONTENT_LENGTH', 0))
        logging.debug(f"Content-Length: {content_length}")
        input_data = sys.stdin.read(content_length) if content_length > 0 else ''
        logging.debug(f"Input data: {input_data}")
        
        try:
            data = json.loads(input_data) if input_data else {}
            logging.debug(f"Parsed JSON: {data}")
        except Exception as e:
            logging.error(f"JSON parsing error: {str(e)}")
            response = {"translatedText": "", "error": f"Invalid JSON: {str(e)}"}
            print(json.dumps(response))
            sys.exit(0)
        
        text = data.get('text', '')
        target = data.get('target', 'en')
        logging.debug(f"Text: {text}, Target: {target}")

        if not text:
            response = {"translatedText": "", "error": "No text provided"}
        elif target not in LANGUAGES:
            response = {"translatedText": "", "error": f"Invalid target language: {target}"}
        else:
            try:
                translator = Translator()
                translated = translator.translate(text, dest=target).text
                logging.debug(f"Translated text: {translated}")
                response = {"translatedText": translated}
            except Exception as e:
                logging.error(f"Translation error: {str(e)}")
                response = {"translatedText": "", "error": f"Translation error: {str(e)}"}
    else:
        logging.debug("Non-POST request received")
        response = {"translatedText": "", "error": "POST method required."}
except Exception as e:
    logging.error(f"Script error: {str(e)}")
    response = {"translatedText": "", "error": f"Script error: {str(e)}"}

print(json.dumps(response))
#!/root/chatbot/venv/bin/python

from controller import Controller
from dotenv import load_dotenv
import json

load_dotenv()

with open('config.json', 'r') as f:
    config = json.load(f)

if config['type'].lower() == 'sentry':
    controller = Controller(config)
    while(True):
        response = controller.prompt()
        controller.say(response)
elif config['type'].lower() == 'webserver':
    from webwrapper import WebWrapper
    server = WebWrapper(config)
    server.run()
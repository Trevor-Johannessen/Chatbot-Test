#!/root/monika/venv/bin/python

from controller import Controller
from dotenv import load_dotenv
import json
import os

load_dotenv()

with open('config.json', 'r') as f:
    config = json.load(f)

    for index, item in enumerate(config['type']):
        if index < len(config['type']) - 1:
            pid = os.fork()
            if pid > 0:
                continue
        if item.lower() == 'sentry':
            controller = Controller(config)
            while(True):
                response = controller.prompt()
                controller.say(response)
        elif item.lower() == 'webserver':
            from webwrapper import WebWrapper
            server = WebWrapper(config)
            server.run()

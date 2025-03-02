#!/root/monika/venv/bin/python

from controller import Controller
from dotenv import load_dotenv
import json
import os
import sys


import argparse

parser = argparse.ArgumentParser(description='Process configuration and environment files.')
parser.add_argument('--config', '-c', default='config.json', help='Path to the configuration file')
parser.add_argument('--env', '-e', default='.env', help='Path to the environment file')
args = parser.parse_args()

load_dotenv(args.env)

with open(args.config, 'r') as f:
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

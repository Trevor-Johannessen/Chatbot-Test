#!/root/chatbot/venv/bin/python

from controller import Controller
from dotenv import load_dotenv

load_dotenv()

controller = Controller(default_interface=False)
controller.initalize_interface(tools=True, variables=True)

while(True):
    controller.prompt()
    

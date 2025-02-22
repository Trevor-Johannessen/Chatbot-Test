#!/root/chatbot/venv/bin/python

from controller import Controller
from dotenv import load_dotenv

load_dotenv()

controller = Controller()
while(True):
    controller.prompt()
    

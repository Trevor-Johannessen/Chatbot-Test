from datetime import datetime

class Default():
    def __init__(self, config):
        self.interface = config['interface']
        self.functions = config['functions']

    def test(self):
        """A test function for when the assistant is asked if they are online or if the client can be heard."""
        self.interface.say_canned("test")

    def start_conversation(self):
        """Sets the ai to enter conversation mode where it will not require a trigger phrase. Only call this if the word conversation is explicitly said."""
        self.interface.say_canned("starting_conversation")
        self.functions['start_conversation']()

    def stop_conversation(self):
        """Sets the ai to leave conversation mode."""
        self.interface.say_canned("stopping_conversation")
        self.functions['stop_conversation']()
    
    def get_time(self):
        """Tells the current time."""
        current_time = datetime.now().strftime("%I:%M %p")
        current_time = current_time.lstrip('0').replace(':0', ':')
        self.interface.say(f"The current time is {current_time}.")
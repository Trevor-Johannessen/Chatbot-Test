from interface import Interface
from inspect import signature, _empty
import json
from datetime import datetime
from mcstatus import JavaServer
import requests

class Controller:
    def __init__(self, default_interface=True):
        self.tools = None
        self.listen_duration = 5
        self.ambient_noise_timeout = 0.2
        self.interface = None
        if default_interface:
            self.interface = Interface()
    def initalize_interface(self, variables=False, tools=False):
        additional_context = ""
        if variables:
            additional_context += '\n\n\nBelow is a JSON containing an array of variables and their datatypes. You may use these values when making function calls.\n'
            additional_context += self.__get_variables()
        if tools:
            self.tools = self.__bundle()
        self.interface = Interface(additional_context)
    def prompt(self):
        message = self.interface.listen(self.listen_duration, self.ambient_noise_timeout)
        #message = input("Prompt: ")
        if not message:
            return
        # Get response
        response = self.interface.prompt(message, tools=self.tools)
        if not response:
            return
        for choice in response.choices:
            if choice.message.tool_calls:
                for tool in choice.message.tool_calls:
                    self.__call_tool(tool)
            if choice.message.content:
                self.interface.say(choice.message.content)
                self.interface.add_context({"role": "assistant", "content": [{"type": "text", "text": choice.message.content}]})
    def __get_variables(self):
        return f'[{{"name": "listen_duration","type": "NUMBER","value":{self.listen_duration}}},{{"name": "ambient_noise_timeout","type": "NUMBER","value": {self.ambient_noise_timeout}}}]'
    def __translate_types(self, type: type):
        types = [x.strip() for x in str(type).split("|")]
        type_list = []
        for type in types:
            if type in ['int']:
                type_list.append({ "type": "integer" })
            elif type in ['float']:
                type_list.append({ "type": "number" })
            elif type in ['bool']:
                type_list.append({ "type": "boolean" })
            elif type in ['list', 'tuple']:
                type_list.append({ "type": "array" })
            elif type in ['str']:
                type_list.append({ "type": "string" })
            else:
                type_list.append({ "type": "object" })
        return type_list
    def __bundle(self):
        if self.tools:
            self.tools
        functions = [func for func in dir(self) if callable(getattr(self, func)) and '__' not in func and func not in ['prompt', 'initalize_interface']]
        tools = []
        for func in functions:
            func_object = getattr(self, func)
            tool={
                'type': 'function',
                'function':{
                    'name': func,
                    'description': func_object.__doc__.split("Variables:", 1)[0].strip(),
                    'parameters': {
                        'type': 'object',
                        'properties': {
                        }
                    },
                    'required': []
                }
            }
            if len(signature(func_object).parameters) > 0:
                var_desc = json.loads(func_object.__doc__.split("Variables:", 1)[1].strip())
                for name, param in signature(func_object).parameters.items():
                    tool['function']['parameters']['properties'][name] = {
                        'anyOf': self.__translate_types(param.annotation),
                        'description': var_desc[name]
                    }
                    if param.default is _empty:
                        tool['function']['required'].append(name)
            tools.append(tool)
        self.tools = tools
        return self.tools
    def __call_tool(self, tool_call):
        try:
            self.interface.clear_recent_context(2)
            args = json.loads(tool_call.function.arguments)
            func = getattr(self, tool_call.function.name)
            func(**args)
        except:
            self.interface.say("Could not call function.")
    def set_variable(self, var: str, value: any):
        """Sets the given variable to the given value.
        Variables:
        {"var":"The name of the variable.","value":"The value to set."}
        """
        setattr(self, var, value)
    def get_variable(self, var: str):
        """Gets the given variable to the given value.
        Variables:
        {"var":"The name of the variable."}
        """
        self.interface.say(f"The value of {var} is {getattr(self, var)}.")
    def add_variable(self, var: str, value: int|float):
        """Adds the {value} parameter to the given variable.
        Variables:
        {"var": "The name of the variable.","value":"The value to add."}
        """
        setattr(self, var, getattr(self,var) + value)
    def subtract_variable(self, var: str, value: int|float):
        """Subtracts the {value} parameter to the given variable.
        Variables:
        {"var": "The name of the variable.","value":"The value to subtract."}
        """
        setattr(self, var, getattr(self,var) - value)
    def save_context(self, filename: str):
        """Saves the current context as the given filename.
        Variables:
        {"filename":"The name of the file to save the context as."}
        """
        self.interface.saveContext(filename)
    def load_context(self, filename: str):
        """Overwrites the current context with the context in the given file.
        Variables:
        {"filename":"The name of the file to load the context from."}
        """
        self.interface.loadContext(filename)
    def clear_context(self):
        """Clears the current context window."""
        self.interface.say("Clearing context.")
        self.interface.clear_context()
    def start_conversation(self):
        """Sets the ai to enter conversation mode where it will not require a trigger phrase. Only call this if the word conversation is explicitly said."""
        self.interface.say("Starting conversation.")
        self.interface.conversing=True
    def stop_conversation(self):
        """Sets the ai to leave conversation mode."""
        self.interface.say("Ending conversation.")
        self.interface.conversing=False
    def get_time(self):
        """Tells the current time."""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.interface.say(f"The time is {current_time}.")
    def change_volume(self, direction: str, delta: int = 1):
        """Changes the volume of output audio.
        Variables:
        {"delta":"The amount to change the volume by.", "direction":"Direction of the volume. Should use the words 'increase' or 'decrease'."}
        """
        print(f"Direction = {direction}, Delta = {delta}")
        if direction.lower() == "decrease":
            endpoint = "volumedown"
        elif direction.lower() == "increase":
            endpoint = "volumeup"
        else:
            self.interface.say("A valid volume direction was not specified.")
        try:
            response = requests.get(f"http://192.168.1.102:8000/{endpoint}?magnitude={delta}")
            if response.status_code != 200:
                raise Exception("")
        except requests.exceptions.RequestException as e:
            self.interface.say(f"Could not adjust volume.")
    def next_song(self):
        """Skips to the next song in the queue."""
        try:
            response = requests.get(f"http://192.168.1.102:8000/music/next")
            if response.status_code != 200:
                raise Exception("")
        except requests.exceptions.RequestException as e:
            self.interface.say(f"Could not skip song.")
    def prev_song(self):
        """Skips to the previous song in the queue."""
        try:
            response = requests.get(f"http://192.168.1.102:8000/music/prev")
            if response.status_code != 200:
                raise Exception("")
        except requests.exceptions.RequestException as e:
            self.interface.say(f"Could not skip song.")
    def toggle_song(self):
        """Pauses or plays the current song."""
        try:
            response = requests.get(f"http://192.168.1.102:8000/music/pause")
            if response.status_code != 200:
                raise Exception("")
        except requests.exceptions.RequestException as e:
            self.interface.say(f"Could not skip song.")
    def minecraft_kick_player(self, player: str = None, reason: str = ""): # should make this an enum for the function I want
        """Kicks a player off the minecraft server.
        Variables:
        {"player":"The player to kick.", "reason":"A message explaining why the player was kicked."}
        """
        try:
            if not player:
                raise Exception("Failed to specify player.")
            player=player.replace(" ", "")
            response = requests.get(f"http://192.168.1.100:8889/minecraft/kick?player={player}&reason={reason}")
            if response.status_code != 200:
                raise Exception("Failed to kick player.")
            self.interface.say(f"Kicked {player}.")
        except requests.exceptions.RequestException as e:
            self.interface.say(f"Could not kick player {player}.")
    def minecraft_ban_player(self, player: str = None, reason: str = ""): # should make this an enum for the function I want
        """Bans a player from the minecraft server.
        Variables:
        {"player":"The player to ban.", "reason":"A message explaining why the player was banned."}
        """
        try:
            if not player:
                raise Exception("Failed to specify player.")
            player=player.replace(" ", "")
            response = requests.get(f"http://192.168.1.100:8889/minecraft/ban?player={player}&reason={reason}")
            if response.status_code != 200:
                raise Exception("Failed to ban player.")
            self.interface.say(f"Banned {player}.")
        except requests.exceptions.RequestException as e:
            self.interface.say(f"Could not ban player {player}.")
    def minecraft_pardon_player(self, player: str = None): # should make this an enum for the function I want
        """Pardons (unbans) a player on the minecraft server.
        Variables:
        {"player":"The player to pardon."}
        """
        try:
            if not player:
                raise Exception("Failed to specify player.")
            player=player.replace(" ", "")
            response = requests.get(f"http://192.168.1.100:8889/minecraft/pardon?player={player}")
            if response.status_code != 200:
                raise Exception("Failed to unban player.")
            self.interface.say(f"Unbanned{player}.")
        except requests.exceptions.RequestException as e:
            self.interface.say(f"Could not unban player {player}.")
    def minecraft_mute_player(self, player: str = None): # should make this an enum for the function I want
        """Mutes a player on the minecraft server.
        Variables:
        {"player":"The player to mute."}
        """
        try:
            if not player:
                raise Exception("Failed to specify player.")
            player=player.replace(" ", "")
            response = requests.get(f"http://192.168.1.100:8889/minecraft/mute?player={player}")
            if response.status_code != 200:
                raise Exception("Failed to mute player.")
            self.interface.say(f"Muted {player}.")
        except requests.exceptions.RequestException as e:
            self.interface.say(f"Could not mute player {player}.")
    def minecraft_unmute_player(self, player: str = None): # should make this an enum for the function I want
        """Unmutes a player on the minecraft server.
        Variables:
        {"player":"The player to unmute."}
        """
        try:
            if not player:
                raise Exception("Failed to specify player.")
            player=player.replace(" ", "")
            response = requests.get(f"http://192.168.1.100:8889/minecraft/unmute?player={player}")
            if response.status_code != 200:
                raise Exception("Failed to unmute player.")
            self.interface.say(f"Unmuted {player}.")
        except requests.exceptions.RequestException as e:
            self.interface.say(f"Could not unmute player {player}.")
    def minecraft_send_message(self, message: str = None): # should make this an enum for the function I want
        """Sends a message to the minecraft server.
        Variables:
        {"message":"The message to send."}
        """
        try:
            if not message:
                raise Exception("Failed to specify message.")
            response = requests.get(f"http://192.168.1.100:8889/minecraft/say?message={message}")
            if response.status_code != 200:
                raise Exception("Failed to send message.")
            self.interface.say(f"Message sent.")
        except requests.exceptions.RequestException as e:
            self.interface.say(f"Could not send message.")
        

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
                for name, param in signature(func_object).parameters.items():
                    tool['function']['parameters']['properties'][name] = {
                        'anyOf': self.__translate_types(param.annotation),
                        'description': func_object.variables[name]
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
            self.interface.say_canned("call_fail")
            print(tool_call.function.name)
            print(args)
    def test(self):
        """A test function for when the assistant is asked if they are online or if the client can be heard."""
        self.interface.say_canned("test")
    def set_variable(self, var: str, value: any):
        """Sets the given variable to the given value."""
        setattr(self, var, value)
    set_variable.variables={"var":"The name of the variable.","value":"The value to set."}
    
    def get_variable(self, var: str):
        """Gets the given variable to the given value."""
        self.interface.say(f"The value of {var} is {getattr(self, var)}.")
    get_variable.variables={"var":"The name of the variable."}

    def add_variable(self, var: str, value: int|float):
        """Adds the {value} parameter to the given variable."""
        setattr(self, var, getattr(self,var) + value)
    add_variable.variables={"var": "The name of the variable.","value":"The value to add."}

    def subtract_variable(self, var: str, value: int|float):
        """Subtracts the {value} parameter to the given variable."""
        setattr(self, var, getattr(self,var) - value)
    subtract_variable.variables={"var": "The name of the variable.","value":"The value to subtract."}

    def save_context(self, filename: str):
        """Saves the current context as the given filename."""
        self.interface.saveContext(filename)
    save_context.variables={"filename":"The name of the file to save the context as."}
    
    def load_context(self, filename: str):
        """Overwrites the current context with the context in the given file."""
        self.interface.loadContext(filename)
    load_context.variables={"filename":"The name of the file to load the context from."}

    def clear_context(self):
        """Clears the current context window."""
        self.interface.say("Clearing context.")
        self.interface.clear_context()

    def start_conversation(self):
        """Sets the ai to enter conversation mode where it will not require a trigger phrase. Only call this if the word conversation is explicitly said."""
        self.interface.say_canned("starting_conversation")
        self.interface.conversing=True

    def stop_conversation(self):
        """Sets the ai to leave conversation mode."""
        self.interface.say_canned("ending_conversation")
        self.interface.conversing=False

    def get_time(self):
        """Tells the current time."""
        current_time = datetime.now().strftime("%H:%M")
        self.interface.say(f"The current time is {current_time}.")

    def change_volume(self, direction: str, delta: int = 1):
        """Changes the volume of output audio."""
        print(f"Direction = {direction}, Delta = {delta}")
        if direction.lower() == "decrease":
            endpoint = "volumedown"
        elif direction.lower() == "increase":
            endpoint = "volumeup"
        else:
            self.interface.say_canned("bad_volume_direction")
        try:
            response = requests.get(f"http://192.168.1.102:8000/{endpoint}?magnitude={delta}")
            if response.status_code != 200:
                raise Exception("")
        except requests.exceptions.RequestException as e:
            self.interface.say_canned("volume_change_fail")
    change_volume.variables={"delta":"The amount to change the volume by.", "direction":"Direction of the volume. Should use the words 'increase' or 'decrease'."}

    def next_song(self):
        """Skips to the next song in the queue."""
        try:
            response = requests.get(f"http://192.168.1.102:8000/music/next")
            if response.status_code != 200:
                raise Exception("")
        except requests.exceptions.RequestException as e:
            self.interface.say_canned("cant_skip_song")

    def prev_song(self):
        """Skips to the previous song in the queue."""
        try:
            response = requests.get(f"http://192.168.1.102:8000/music/prev")
            if response.status_code != 200:
                raise Exception("")
        except requests.exceptions.RequestException as e:
            self.interface.say_canned("cant_skip_song")

    def toggle_song(self):
        """Pauses or plays the current song."""
        try:
            response = requests.get("http://192.168.1.102:8000/music/pause")
            if response.status_code != 200:
                raise Exception("")
        except requests.exceptions.RequestException as e:
            self.interface.say(f"Could not skip song.")

    def minecraft_kick_player(self, player: str = None, reason: str = ""): # should make this an enum for the function I want
        """Kicks a player off the minecraft server."""
        try:
            if not player:
                raise Exception("specify_player")
            player=player.replace(" ", "")
            response = requests.get(f"http://192.168.1.100:8889/minecraft/kick?player={player}&reason={reason}")
            if response.status_code != 200:
                raise Exception("kick_failed")
            self.interface.say(f"Kicked {player}.")
        except Exception as e:
            self.interface.say_canned(e)
    minecraft_kick_player.variables={"player":"The player to kick.", "reason":"A message explaining why the player was kicked."}

    def minecraft_ban_player(self, player: str = None, reason: str = ""): # should make this an enum for the function I want
        """Bans a player from the minecraft server."""
        try:
            if not player:
                raise Exception("specify_player")
            phonetic_name=player 
            player=player.replace(" ", "")
            response = requests.get(f"http://192.168.1.100:8889/minecraft/ban?player={player}&reason={reason}")
            if response.status_code != 200:
                raise Exception("ban_failed")
            self.interface.say(f"Banned {phonetic_name}.")
        except Exception as e:
            self.interface.say_canned(e)
    minecraft_ban_player.variables={"player":"The player to ban.", "reason":"A message explaining why the player was banned."}

    def minecraft_pardon_player(self, player: str = None): # should make this an enum for the function I want
        """Pardons (unbans) a player on the minecraft server."""
        try:
            if not player:
                raise Exception("specify_player")
            phonetic_name=player 
            player=player.replace(" ", "")
            response = requests.get(f"http://192.168.1.100:8889/minecraft/pardon?player={player}")
            if response.status_code != 200:
                raise Exception("pardon_failed")
            self.interface.say(f"Unbanned {phonetic_name}.")
        except Exception as e:
            self.interface.say_canned(e)
    minecraft_pardon_player.variables={"player":"The player to pardon."}

    def minecraft_mute_player(self, player: str = None): # should make this an enum for the function I want
        """Mutes a player on the minecraft server."""
        try:
            if not player:
                raise Exception("specify_player")
            phonetic_name=player
            player=player.replace(" ", "")
            response = requests.get(f"http://192.168.1.100:8889/minecraft/mute?player={player}")
            if response.status_code != 200:
                raise Exception("mute_failed")
            self.interface.say(f"Muted {phonetic_name}.")
        except Exception as e:
            self.interface.say_canned(e)
    minecraft_mute_player.variables={"player":"The player to mute."}

    def minecraft_unmute_player(self, player: str = None): # should make this an enum for the function I want
        """Unmutes a player on the minecraft server."""
        try:
            if not player:
                raise Exception("specify_player")
            phonetic_name=player 
            player=player.replace(" ", "")
            response = requests.get(f"http://192.168.1.100:8889/minecraft/unmute?player={player}")
            if response.status_code != 200:
                raise Exception("failed_unmute")
            self.interface.say(f"Unmuted {phonetic_name}.")
        except Exception as e:
            self.interface.say_canned(e)
    minecraft_unmute_player.variables={"player":"The player to unmute."}

    def minecraft_send_message(self, message: str = None): # should make this an enum for the function I want
        """Sends a message to the minecraft server."""
        try:
            if not message:
                raise Exception("specify_message")
            response = requests.get(f"http://192.168.1.100:8889/minecraft/say?message={message}")
            if response.status_code != 200:
                raise Exception("message_failed")
            self.interface.say_canned(f"message_sent")
        except Exception as e:
            self.interface.say(e)
    minecraft_send_message={"message":"The message to send."}

    def get_minecraft_status(self, list_players: bool = False): # should make this an enum for the function I want
        """Gets the number of players or list of players currently on my minecraft server."""
        server = JavaServer.lookup("mc.sector-alpha.net")
        response = ""
        try:
            status = server.status()
            player_count = status.players.online
            player_list = [player.name for player in status.players.sample] if status.players.sample else []
            if status.players.online == 0:
                self.interface.say_canned("nobody_online")
                return
            elif list_players and player_count == 1:
                response = f"{player_list[0]} is currently online."
            elif list_players:
                response = ",\n".join(player_list) + " are currently online."
            elif player_count == 1:
                response = f"There is currently {player_count} person online."
            else:
                response = f"There are currently {player_count} people online."
            self.interface.say(response)
        except Exception as e:
            print(e)
            self.interface.say_canned("server_offline")
    get_minecraft_status.variables={"list_players":"Respond with a list of online players instead of a number."}
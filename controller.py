from interface import Interface
from inspect import signature, _empty
import json
import re

class Controller:
    def __init__(self, default_interface=True):
        self.tools = None
        self.listen_duration = 5
        self.ambient_noise_timeout = 0.2
        self.interface = None
        if default_interface:
            self.interface = Interface()
    def custom_interface(self, tools=False, variables=False):
        additional_context = ""
        if variables:
            additional_context += '\n\n\nBelow is a JSON containing an array of variables and their datatypes. You may use these values when making function calls.\n'
            additional_context += self.__get_variables()
            additional_context += '\n\n'
        if tools:
            self.__bundle()
            additional_context += '\nIf you do not think the user wants you to execute a command, ignore the remainder of this line and answer conversationally! Below is a JSON provided in Open-AIs tool declaration schema which denotes function calls you can make. If you believe the user wants you to make a function call, only output a json in the following syntax [{"function": "(function name)", "parameters": {{"(parameter name)": (parameter value)}}]. The parameters section can have multiple elements. Replace the parenthesis with values.\n'
            #additional_context += "\nBelow is a JSON provided in Open-AIs tool declaration schema which denotes function calls you can make. If you believe the user wants you to make a function call, only output a json containing an array of maps containing the function name and a map of variable names to their value.\n"
            additional_context += json.dumps(self.tools)
        self.interface = Interface(additional_context)
    def prompt(self):
        #message = self.interface.listen()
        message = input("Prompt: ")
        if message:
            self.interface.fenceposting = True
            # Get response
            response = self.interface.prompt(message)
            message = response.message.content

            # Get think portion
            think_start = message.find("<think>") + len("<think>")
            think_end = message.find("</think>")
            think = message[think_start:think_end] if think_start != -1 and think_end != -1 else ""

            # Get chat portion
            chat = message[think_end+len("</think>\n\n"):]

            # check for commands to run here
            found_json=False
            try:
                # Attempt to find and parse JSON within the chat string
                json_start = chat.find("{")
                json_end = chat.rfind("}") + 1
                if json_start != -1 and json_end != -1:
                    potential_json = chat[json_start:json_end]
                    parsed_json = json.loads(potential_json)
                    print("Captured JSON:", parsed_json)
                    found_json=True
                    self.interface.context.pop()
            except json.JSONDecodeError:
                print("Invalid JSON format found in chat.")
                self.interface.say("Invalid JSON format found in chat.")
            if not found_json:
                print(chat)
                self.interface.say(chat)
    def __get_variables(self):
        return f'[{{"name": "listen_duration","type": "NUMBER","value":{self.listen_duration}}},{{"name": "ambient_noise_timeout","type": "NUMBER","value": {self.ambient_noise_timeout}}}]'
    def __translate_type(self, type: type):
        if type in [int]:
            return "integer"
        elif type in [float]:
            return "number"
        elif type in [bool]:
            return "boolean"
        elif type in [list, tuple]:
            return "array"
        elif type in [str]:
            return "string"
        else:
            return "object"

    def __bundle(self):
        if self.tools:
            self.tools
        functions = [func for func in dir(self) if callable(getattr(self, func)) and '__' not in func and func not in ['prompt', 'custom_interface']]
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
            var_desc = json.loads(func_object.__doc__.split("Variables:", 1)[1].strip())
            for name, param in signature(func_object).parameters.items():
                tool['function']['parameters']['properties'][name] = {
                    'type': self.__translate_type(param.annotation),
                    'description': var_desc[name]
                }
                if param.default is _empty:
                    tool['function']['required'].append(name)
            tools.append(tool)
        self.tools = tools
        return self.tools
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
        getattr(self, var)
    def add_variable(self, var: str, value: any):
        """Adds the {value} parameter to the given variable.
        Variables:
        {"var": "The name of the variable.","value":"The value to add."}
        """
        setattr(self, var, getattr(self,var) + value)
    def subtract_variable(self, var: str, value: any):
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
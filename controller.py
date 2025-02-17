from interface import Interface
from inspect import signature, _empty
import json
from datetime import datetime

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
        #self.interface.fenceposting = True
        # Get response
        response = self.interface.prompt(message, tools=self.tools)
        if not response:
            return
        for choice in response.choices:
            if choice.message.tool_calls:
                for tool in choice.message.tool_calls:
                    self.__call_tool(tool)
            if choice.message.content:
                print(response.choices[0].message.content)
                self.interface.say(response.choices[0].message.content)
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
            self.interface.context.pop()
            args = json.loads(tool_call.function.arguments)
            func = getattr(self, tool_call.function.name)
            func(**args)
        except:
            print("Could not call function.")
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
    def start_conversation(self):
        """Sets the ai to enter conversation mode where it will not require a trigger phrase."""
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
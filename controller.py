from interface import Interface
from inspect import signature, _empty, getmembers, isclass
import json
from importlib import import_module

class Controller:
    def __init__(self, config):
        
        self.names = [name.lower() for name in config['names']]
        self.listen_duration = config['listen_duration']
        self.ambient_noise_timeout = config['ambient_noise_timeout']
        self.modules = [module.lower() for module in config['modules']]
        self.context = config['context']
        self.mode = config['mode'].lower() if 'mode' in config else "voice"

        if "default" not in self.modules:
            print("Warning: 'default' module not included in modules.")

        self.context += "\n\n"
        self.classes = []
        self.interface = Interface(
            names=self.names,
            context=self.context,
            mode=self.mode,
            context_window=config['context_window'],
            history=config['voice_history_directory'],
            voice_id=config['voice_id']
        )
        for module_name in self.modules:
            module_name_literal = f"modules.{module_name}"
            module = import_module(module_name_literal)
            classes = getmembers(module, isclass)
            for _, cls in classes:
                if cls.__module__ != module_name_literal:
                    continue
                self.classes.append(cls(self.interface, config))
                if hasattr(cls, 'context'):
                    self.context += f"{cls.context(config)}\n\n"
        self.interface.initalize_context(self.context)
        self.tools = self.__bundle()

    def prompt(self, text=None, audio_file=None):
        message = self.interface.listen(self.listen_duration, self.ambient_noise_timeout, text=text, audio_file=audio_file)
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
                self.interface.add_context({"role": "assistant", "content": [{"type": "text", "text": choice.message.content}]})
                return choice.message.content
            
    def say(self, message):
        self.interface.say(message)

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
        functions = []
        tools = []
        for cls in self.classes:
            functions = [func for func in dir(cls) if callable(getattr(cls, func)) and '__' not in func and func not in ['context']]
            for func in functions:
                func_object = getattr(cls, func)
                tool={
                    'type': 'function',
                    'function':{
                        'name': func,
                        'description': func_object.__doc__,
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
        self.interface.clear_recent_context(2)
        args = json.loads(tool_call.function.arguments)
        for cls in self.classes:
            if hasattr(cls, tool_call.function.name):
                func = getattr(cls, tool_call.function.name)
                func(**args)
                return
        self.interface.say_canned("call_fail")
        print(tool_call.function.name)
        print(args)
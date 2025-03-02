from interface import Interface
from inspect import signature, _empty, getmembers, isclass
import json
from importlib import import_module
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Controller:
    def __init__(self, config):
        logging.basicConfig(filename=f"{config['log_directory']}/latest.log", level=logging.INFO)
        self.names = [name.lower() for name in config['names']]
        self.listen_duration = config['listen_duration']
        self.ambient_noise_timeout = config['ambient_noise_timeout']
        self.modules = [module.lower() for module in config['modules']]
        self.inital_context = config['context']
        self.mode = config['mode'].lower() if 'mode' in config else "voice"
        self.config = config

        if "default" not in self.modules:
            logger.warning("Warning: 'default' module not included in modules.")

        self.classes = []
        self.interface = Interface(
            log_directory=config['log_directory'],
            names=self.names,
            context=self.inital_context,
            mode=self.mode,
            context_window=config['context_window'],
            history=config['voice_history_directory'],
            voice_id=config['voice_id']
        )
        
        config['interface'] = self.interface
        config['functions'] = {
            "prompt": self.prompt,
            "say": self.say,
            "get_input": self.get_input
        }
        for module_name in self.modules:
            module_name_literal = f"modules.{module_name}"
            module = import_module(module_name_literal)
            classes = getmembers(module, isclass)
            for _, cls in classes:
                if cls.__module__ != module_name_literal:
                    continue
                self.classes.append(cls(config))
        self.refresh_context()
        self.tools = self.__bundle()

    def refresh_context(self):
        context=f"{self.inital_context}\n\n"
        for cls in self.classes:
            if hasattr(cls, 'context'):
                context += f"{cls.context(self.config)}\n\n"
        self.interface.refresh_context(context)

    def get_input(self, audio_file=None):
        return self.interface.get_input(self.listen_duration, self.ambient_noise_timeout, audio_file=audio_file)

    def prompt(self, text=None, audio_file=None):
        if not text:
            text = self.get_input(audio_file=audio_file)
        message = self.interface.parse_text(text)
        if not message:
            return
        self.refresh_context()
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
        args = json.loads(tool_call.function.arguments)
        for cls in self.classes:
            if hasattr(cls, tool_call.function.name):
                func = getattr(cls, tool_call.function.name)
                func(**args)
                self.interface.clear_recent_context()
                return
        self.interface.say_canned("call_fail")
        logger.error(f"Could not call function {tool_call.function.name} with args {args}")

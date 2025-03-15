from interface import Interface
from inspect import signature, _empty, getmembers, isclass
import json
from importlib import import_module
from datetime import datetime
import logging
import os
import schedule
from time import sleep
from enum import Enum

logger = logging.getLogger(__name__)


class HookType(Enum):
    STARTUP = "_startup"
    SHUTDOWN = "_shutdown"
    CONTEXT = "_context"

class Controller:
    def __init__(self, config):
        # Set up logging
        log_directory = config['log_directory']
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        log_file = f"{log_directory}/latest.log"
        if not os.path.exists(log_file):
            open(log_file, 'w').close()
        logging.basicConfig(filename=log_file, level=logging.INFO)

        # Declare variables
        self.names = [name.lower() for name in config['names']]
        self.modules = [module.lower() for module in config['modules']]
        self.inital_context = config['context']
        self.mode = config['mode'].lower() if 'mode' in config else "voice"
        self.config = config
        self._checking_jobs = False

        # Warnings
        if "default" not in self.modules:
            logger.warning("Warning: 'default' module not included in modules.")

        # Load interface
        self.interface = Interface(
            log_directory=config['log_directory'],
            mode=self.mode,
            context_window=config['context_window'],
            voice_directory=config['voice_directory'],
            voice_id=config['voice_id'],
            listen_duration=config['listen_duration'],
            ambient_noise_timeout=config['ambient_noise_timeout']
        )
        
        # Set aditional info for modules
        config['interface'] = self.interface
        config['functions'] = {
            "prompt": self.prompt,
            "new_context": self.new_context,
        }
        self.config['enabled_modules'] = self.modules

        # Load modules
        self.classes = []
        for module_name in self.modules:
            module_name_literal = f"modules.{module_name}"
            module = import_module(module_name_literal)
            classes = getmembers(module, isclass)
            for _, cls in classes:
                if cls.__module__ != module_name_literal:
                    continue
                self.classes.append(cls(self.config))

        # Set up contexts
        context = self.inital_context + "\n\n"
        context += "\n\n".join(self._fire_hook(HookType.CONTEXT))
        self.interface.refresh_context(context)
        self.tools = self.__bundle()

        # Run post init hooks
        self.config['classes'] = self.classes
        self._fire_hook(HookType.STARTUP)

    def _fire_hook(self, type: HookType):
        outputs = []
        for cls in self.classes:
            if hasattr(cls, type.value):
                out = getattr(cls, type.value)(self.config)
                if out:
                    outputs.append(out)
        return outputs

    def new_context(self, blank_context=False):
        additional_context=""
        if not blank_context:
            additional_context = "\n\n".join(self._fire_hook(HookType.CONTEXT))
        context = self.interface.new_context(additional_context)
        return context

    def prompt(self, text=None, context: list = None, tools=None):
        # Check jobs
        if not self._checking_jobs:
            self._checking_jobs = True
            schedule.run_pending()
            self._checking_jobs = False
            next_job = schedule.idle_seconds()
            listen_duration = self.interface.listen_duration
            if next_job < listen_duration*2:
                listen_duration = next_job
        if not text:
            return
        # Manage context
        additional_context = "\n\n".join(self._fire_hook(HookType.CONTEXT))
        self.interface.refresh_context(additional_context)
        # Check if custom tools are used
        if tools == None:
            tools = self.tools
        if tools == []:
            tools = None
        # Get response
        response = self.interface.prompt(text, tools=tools, context=context)
        if not response:
            return
        for choice in response.choices:
            if choice.message.tool_calls:
                for tool in choice.message.tool_calls:
                    self.__call_tool(tool)
            if choice.message.content:
                return choice.message.content

    def converse(self, audio_file=None, silence=False):
        text = self.interface.get_input(audio_file=audio_file)
        if not text:
            return
        found_name=False
        text_low = text.lower()
        for name in self.names:
            if name in text_low:
                found_name=True
                break
        if not found_name:
            return
        response = self.prompt(text)
        if response:
            self.interface.add_context({"role": "assistant", "content": [{"type": "text", "text": response}]})
            if not silence:
                self.interface.say(response)
            return response

    def _translate_types(self, type: type):
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
            functions = [func for func in dir(cls) if callable(getattr(cls, func)) and not func.startswith('_')]
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
                            'anyOf': self._translate_types(param.annotation),
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

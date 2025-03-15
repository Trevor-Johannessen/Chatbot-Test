import speech_recognition as sr
from openai import OpenAI
import os
import io
import json 
import shutil
import random
from time import sleep
from elevenlabs import play, save
from elevenlabs.client import ElevenLabs
from datetime import datetime
from signal import signal, SIGINT, SIGTERM, SIGUSR1
import logging
import sys
import select

logger = logging.getLogger(__name__)

class Interface:
    def __init__(
            self,
            log_directory: str,
			mode: str = "voice",
			context_window: int = 5,
			context: str = "",
			voice_directory: str = "./voice",
			voice_id: str = "29vD33N1CtxCmqQRPOHJ",
            ambient_noise_timeout: float = 0.2,
            listen_duration: float = 10,
        ):
        logging.basicConfig(filename="f{log_directory}/latest.log", level=logging.INFO)

        if ambient_noise_timeout <= 0 or listen_duration <= 0:
            logging.critical("Ambient noise timeout and listen duration must be positive, non-zero numbers.")
            raise "Interface Exception: Ambient noise timeout and listen duration must be positive, non-zero numbers."

        # Start sliding context window
        if context_window > 0:
            timer_pid = os.fork()
            if timer_pid == 0:
                self.__timer(context_window)

        self._recognizer = sr.Recognizer() 
        self.affirmations = ["yes", "yeah", "yep", "confirm", "affirmative", "correct", "accept"]
        self.quit_terms = ["cancel", "quit", "stop", "exit", "return", "no", "nope", "nada", "nah"]
        self.context = None
        self.prompt_displayed = False
        self.base_context = context
        self._voice_id = voice_id
        self._voice_dir = voice_directory
        self.ambient_noise_timeout = ambient_noise_timeout
        self.listen_duration = listen_duration
        self.mode = mode
        self._last_message = datetime.now()
        self._client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        self._voice = ElevenLabs(
            api_key=os.environ.get("ELEVENLABS_API_KEY")
        )
        signal(SIGUSR1, self.clear_context)
        signal(SIGINT, self.terminate)
        signal(SIGTERM, self.terminate)
        self.refresh_context(context)
        self.say_canned("hello_world")

    def new_context(self, new_inital_context=""):
        return [{"role": "system", "content": [{"type": "text", "text": new_inital_context}]}]
    
    def refresh_context(self, new_inital_context=""):
        if self.context == None or len(self.context) < 1:
            self.context = [1]
        self.context[0] = self.new_context(new_inital_context)[0]

    def add_context(self, new):
        self.context.append(new)

    def clear_context(self, sig=None, frame=None):
        self.context = None
        self.refresh_context(self.base_context)
    
    def clear_recent_context(self, i=1):
        self.context = self.context[:-i]
    
    def clear_last_prompt(self):
        for i in range(len(self.context)-1, 0, -1):
            if self.context[i]['role'] == 'user':
                self.context = self.context[:i] + self.context[i+1:]
                return

    def get_input(self, audio_file=None):
        if self.mode == "voice" or audio_file:
            return self._get_input_voice(audio_file=audio_file)
        elif self.mode == "text":
            return self._get_input_text()
        return None

    def _get_input_text(self):
            if not self.prompt_displayed:
                print("Prompt: ", end='', flush=True)
                self.prompt_displayed = True
            ready, _, _ = select.select([sys.stdin], [], [], 1)
            if ready:
                self.prompt_displayed = False
                return sys.stdin.readline().strip()
            return None

    def _get_input_voice(self, audio_file=None):
        if audio_file == None:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=self.ambient_noise_timeout)
                audio = self._recognizer.listen(source, phrase_time_limit=self.listen_duration)
        elif audio_file:
            audio = sr.AudioFile(audio_file)
            with audio as source:
                audio = self._recognizer.record(audio)
        if audio:
            try: # Too much noise gives an Exception
                text = self._recognizer.recognize_google(audio)
            except:
                text=None
        logging.info(text)
        return text

    def prompt(self, message, tools=None, context=None):
        if context:
            context.append({"role": "user", "content": [{"type": "text", "text": message}]})
        else:
            self.context.append({"role": "user", "content": [{"type": "text", "text": message}]})
            context = self.context
        response = self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=context,
            tools=tools
        )
        return response
    
    def generate_voice(self, message):
        if message == None:
            return
        audio = self._voice.text_to_speech.convert(
            text=message,
            voice_id=self._voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        time = datetime.now()
        filename = f"{self._voice_dir}/history/{time}.mp3"
        pid = os.fork() # Copying stream is difficult, so I will copy everything
        if pid == 0:
            save(audio, filename)
            exit(0)
        return audio, filename
    
    def say(self, message):
        if not message:
            return
        self._last_message = datetime.now()
        if isinstance(message, io.BufferedReader):
            if self.mode == "voice":
                play(message)
            return
        logging.info(f"Saying: {message}")
        if self.mode == "voice":
            audio, _ = self.generate_voice(message)
            play(audio)
        else:
            print(message)

    def say_canned(self, name):
        logging.info(f"Saying canned: {name}")
        dir_path=f"{self._voice_dir}/canned_lines/{name}"
        lines = []
        for filename in os.listdir(dir_path):
            path = os.path.join(dir_path, filename)
            if os.path.isfile(path):
                lines.append(path)
        if len(lines) <= 0:
            path="./audio/canned_lines/unknown_error.mp3"
        else:
            path = random.choice(lines)
        with open(path, "rb") as line:
            self.say(line)

    def load_context(self, file):
        if not os.path.isfile(f"contexts/{file}"):
            self.say_canned("fail_not_exist")
            return
        with open(f"contexts/{file}", "r") as file:
            self.context = json.loads(file.read())

    def save_context(self, filename):
        if not filename:
            self.say_canned("save_context")
            filename = self.listen()
        if filename in self._quit_terms:
            return
        if os.path.isfile(f"contexts/{filename}"):
            self.say_canned("file_exists_replace")
            confirmation = self.listen()
            if confirmation not in self._affirmations:
                return
        with open(f"contexts/{filename}", "w+") as file:
            file.write(json.dumps(self.context))
        self.say_canned("file_saved")

    def terminate(self, sig=None, frame=None):
        self.say_canned("goodbye")
        exit(1)

    def __timer(self, window: float = 5):
        while True:
            sleep(window*60)
            os.kill(os.getppid(), SIGUSR1)

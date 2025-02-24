import speech_recognition as sr
from openai import OpenAI
import os
import io
import json 
import shutil
from time import sleep
from elevenlabs import play, save
from elevenlabs.client import ElevenLabs
from datetime import datetime
from signal import signal, SIGINT, SIGTERM, SIGUSR1

class Interface:
    def __init__(self, names: list = ["monika", "monica"], mode: str = "voice", context_window: int = 5, context: str = "", history: str = "./", voice_id: str = "29vD33N1CtxCmqQRPOHJ"):
        if len(names) == 0:
            raise "Interface Exception: Names needs at least one element."
        
        timer_pid = os.fork()
        if timer_pid == 0:  # Child process
            self.__timer(context_window)

        self.recognizer = sr.Recognizer() 
        self.conversing = False
        self.standby = False
        self.affirmations = ["yes", "yeah", "yep", "confirm", "affirmative", "correct", "accept"]
        self.quit_terms = ["cancel", "quit", "stop", "exit", "return"]
        self.context = []
        self.base_context = context
        self.names = names
        self.voice_id = voice_id
        self.history = history
        self.mode = mode
        self.inital_context = context
        self.last_message = datetime.now()
        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        self.voice = ElevenLabs(
            api_key=os.environ.get("ELEVENLABS_API_KEY")
        )
        signal(SIGUSR1, self.clear_context)
        signal(SIGINT, self.terminate)
        signal(SIGTERM, self.terminate)
        self.initalize_context(context)
        self.say_canned("hello_world")
    def initalize_context(self, context):
        self.context = [{"role": "system", "content": [{"type": "text", "text": f"Your name is {self.names[0]}. {context}"}]}]
    def listen(self, listen_duration, ambient_noise_timeout):
        if self.mode == "text":
            self.standby = True
            return input("Prompt: ")
        print("Listening")
        try:
            with sr.Microphone() as source2:
                self.recognizer.adjust_for_ambient_noise(source2, duration=ambient_noise_timeout)
                audio2 = self.recognizer.listen(source2, phrase_time_limit=listen_duration)
                text = self.recognizer.recognize_google(audio2)
                text = text.lower()
                words = text.split(' ')
                print(words)
                if "start conversation" in text:
                    self.conversing = True
                    self.say_canned("starting_conversation")
                    return
                elif "stop conversation" in text:
                    self.conversing = False
                    self.say_canned("stopping_conversation")
                elif any(name in words for name in self.names):
                    self.standby = True
                return text
        except Exception as e:
            print(f"Listen exception: {e}")
    def prompt(self, message, tools=None):
        if not self.conversing and not self.standby:
            return
        if self.standby:
            self.standby = False
        self.context.append({"role": "user", "content": [{"type": "text", "text": message}]})
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.context,
            tools=tools
        )
        return response
    def say(self, message):
        if not message:
            return
        self.last_message = datetime.now()
        if isinstance(message, io.BufferedReader):
            if self.mode == "voice":
                play(message)
            return
        print(f"Saying:\t{message}")
        if self.mode != "voice":
            return
        audio = self.voice.text_to_speech.convert(
            text=message,
            voice_id=self.voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        time = datetime.now()
        temp_filename = f"./{time}.mp3"
        filename = f"{self.history}/{time}.mp3"
        save(audio, temp_filename)
        with open(temp_filename, "rb") as speech:
            play(speech)
        shutil.copy(temp_filename, filename)
        os.remove(temp_filename)
    def say_canned(self, name):
        print(f"Saying: {name}")
        path=f"./audio/canned_lines/{name}.mp3"
        if not os.path.isfile(path):
            path="./audio/canned_lines/unknown_error.mp3"
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
        if filename in self.quit_terms:
            return
        if os.path.isfile(f"contexts/{filename}"):
            self.say_canned("file_exists_replace")
            confirmation = self.listen()
            if confirmation not in self.affirmations:
                return
        with open(f"contexts/{filename}", "w+") as file:
            file.write(json.dumps(self.context))
        self.say_canned("file_saved")
    def add_context(self, new):
        self.context.append(new)
    def clear_context(self, sig=None, frame=None):
        self.initalize_context(self.base_context)
    def clear_recent_context(self, i):
        self.context = self.context[:-i]
    def terminate(self, sig=None, frame=None):
        self.say_canned("goodbye")
        exit(1)
    def __timer(self, window: float = 5):
        while True:
            sleep(window*60)
            os.kill(os.getppid(), SIGUSR1)

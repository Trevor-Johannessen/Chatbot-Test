import speech_recognition as sr
#from openai import OpenAI
import ollama
import pyttsx3
import os
import json 
from itertools import chain


class Interface:
    def __init__(self, extra_context=""):
        self.recognizer = sr.Recognizer() 
        self.conversing = False
        self.fenceposting = False
        self.affirmations = ["yes", "yeah", "confirm", "affirmative", "correct", "accept"]
        self.quit_terms = ["cancel", "quit", "stop", "exit", "return"]
        self.context = []
        # self.client = OpenAI(
        #     api_key=os.environ.get("OPENAI_API_KEY"),
        # )
        self.speech_engine = pyttsx3.init()
        self.initalizeContext(extra_context)
        self.say("Hello world.")

    def initalizeContext(self, extra_context=""):
        self.context = [{"role": "system", "content": f"""You are a helpful assistant and program controller. Please try to be concise and keep responses to two sentences or less. {extra_context}"""}]

    def listen(self):
        print("Listening")
        try:
            with sr.Microphone() as source2:
                self.recognizer.adjust_for_ambient_noise(source2, duration=self.ambient_noise_timeout)
                audio2 = self.recognizer.listen(source2, phrase_time_limit=self.listen_duration)
                
                text = self.recognizer.recognize_google(audio2)
                text = text.lower()
                words = text.split(' ')
                print(words)
                if "start conversation" in text:
                    self.conversing = True
                    self.say("Starting conversation.")
                    return
                elif "stop conversation" in text:
                    self.conversing = False
                    self.say("Stopping conversation.")
                elif len(words) > 1 and (words[0] == 'fence' and words[1] == 'post'):
                    self.fenceposting = True
                    text = text[len(words[0])+len(words[1])+2:]
                return text
        except Exception as e:
            print(f"Listen exception: {e}")
            
    def prompt(self, message, tools=None):
        if not self.conversing and not self.fenceposting:
            return
        if self.fenceposting:
            self.fenceposting = False

        self.context += [{"role": "user", "content": message}]
        response = ollama.chat(
            model="deepseek-r1:7b",
            messages=self.context,
            tools=tools
        )
        return response
    
    def say(self, message):
        if not message:
            return
        self.speech_engine.say(message) 
        self.speech_engine.runAndWait()

    def loadContext(self, file):
        if not os.path.isfile(f"contexts/{file}"):
            self.say("This file does not exist.")
            return
        with open(f"contexts/{file}", "r") as file:
            self.context = json.loads(file.read())

    def saveContext(self, filename):
        if not filename:
            self.say("What would you like to save this context as?")
            filename = self.listen()
        if filename in self.quit_terms:
            return
        if os.path.isfile(f"contexts/{filename}"):
            self.say("This file already exists. Replace it?")
            confirmation = self.listen()
            if confirmation not in self.affirmations:
                return
        with open(f"contexts/{filename}", "w+") as file:
            file.write(json.dumps(self.context))
        self.say("File saved.")
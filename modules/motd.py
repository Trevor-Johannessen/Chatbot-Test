import schedule
from datetime import datetime
from modules.weather import Weather
from modules.notes import Notes
import pytz

class Motd():
    def __init__(self, config):
        self.client_name = config['client_name'] if 'client_name' in config else None
        self.interface = config['interface']
        self.functions = config['functions']
        self.city = config['city']
        self.country = config['country_code']
        self.modules = config['modules']

        schedule.every().day.at(config['motd_time'], config['timezone']).do(self.__say_motd)

    def _post_init(self, config):
        
        for cls in config['classes']:
            if isinstance(cls, Weather):
                self.weather = cls
            elif isinstance(cls, Notes):
                pass


    def __say_motd(self):
        context = self.functions['get_new_context']()

        # Get neccesary information
        current_time = datetime.now().strftime("%B %d, %Y, %I:%M %p")
        if self.city and self.weather:
            # Get information about the weather
            weather = self._get_weather(self.city, self.country_code)
            weather_description = self._get_weather_description(weather)
            weather_prompt += "\n\nBelow is a list of attributes about the weather which can help answer this prompt."
            for var in weather_description:
                weather_prompt+=f"\n{var}"
            
        notes = None
        if "notes" in self.modules:
            notes = """
                Below is today's todo list:
            """

        # Built prompt
        prompt = ""
        footer=""
        if self.client_name:
            prompt+=f"Greet the user (named {self.client_name}) a good morning. "
        if weather_prompt:
            prompt+=f"Tell them about the weather in {self.city} for today.\n"
            footer+=f"{weather_prompt}\n\n"
        prompt+=f"Tell them the date and time in that order (it is currently {current_time}). "
        if notes:
            prompt+=f"Summarize the items they have on their todo list for today (seen below), if there are no items tell them they have nothing on their todo list for today. "
            footer+=notes
        self.interface.prime()
        message = self.functions['prompt'](text=f"{prompt}\n\n\n{footer}", context=context, skip_context=True, tools=[])
        if message:
            self.interface.say(message)

    def read_motd(self):
        """Reads off the message of the day."""
        self.__say_motd()

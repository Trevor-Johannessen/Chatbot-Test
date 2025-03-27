import schedule
from datetime import datetime
from modules.weather import Weather
from modules.notes import Notes
from text_transformers import TextTransformer

class Motd():
    def __init__(self, config):
        self.client_name = config['client_name'] if 'client_name' in config else None
        self.interface = config['interface']
        self.functions = config['functions']
        self.city = config['city']
        self.country = config['country_code']
        self.modules = config['modules']

        schedule.every().day.at(config['motd_time'], config['timezone']).do(self.__say_motd)

    def _startup(self, config):
        
        for cls in config['classes']:
            if isinstance(cls, Weather):
                self.weather = cls
            elif isinstance(cls, Notes):
                self.notes = cls


    def __say_motd(self):
        context = self.functions['new_context']()

        # Get neccesary information
        today = datetime.now()
        current_time = today.strftime("%I:%M %p")
        current_date = today.strftime("%B %d, %Y")
        if getattr(self, 'city') and getattr(self, 'weather'):
            # Get information about the weather
            weather = self.weather._get_weather(self.city, self.country)
            weather_description = self.weather._get_weather_description(weather)
            weather_prompt = "\n\nBelow is a list of attributes about the weather which can help answer this prompt."
            for var in weather_description:
                weather_prompt+=f"\n{var}"
            
        notes = None
        if getattr(self, 'notes'):
            todays_notebook = self.notes._get_todo_name(today.day, today.month, today.year)
            all_notes = [note[1] for note in self.notes._get_all_notes(todays_notebook)]
            notes = """
                Below is today's todo list:\n
            """
            for note in all_notes:
                notes += f"{note}\n"

        # Built prompt
        prompt = ""
        footer=""
        if self.client_name:
            current_hour = datetime.now().hour
            time_of_day = "morning" if current_hour < 12 else "afternoon" if current_hour < 17 else "evening"
            prompt+=f"Greet the user a good {time_of_day}. "
        if weather_prompt:
            prompt+=f"Tell them about the weather in {self.city} for today.\n"
            footer+=f"{weather_prompt}\n\n"
        prompt+=f"Tell them the time and date in that order (it is currently {current_time}, {current_date}). "
        if notes:
            prompt+=f"Summarize the items they have on their todo list for today (seen below), if there are no items tell them they have nothing on their todo list for today. "
            footer+=notes
        
        message = self.functions['prompt'](text=f"{prompt}\n\n\n{footer}", context=context, tools=[])
        if message:
            message = TextTransformer.units(message)
            self.interface.say(message)

    def read_motd(self):
        """Reads off the message of the day."""
        self.__say_motd()

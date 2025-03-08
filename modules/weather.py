from datetime import datetime
from pyowm import OWM
import pytz
import os

class Weather():
    def __init__(self, config):
        self.interface = config['interface']
        self.functions = config['functions']
        self.owm = OWM(os.environ['OWM_API_KEY'])
        self.mgr = self.owm.weather_manager()
        self.timezone = tz = pytz.timezone(config['timezone'])
        self.imperial = False
        if 'use_imperial' in config:
            self.imperial = config['use_imperial']
        self.symbol = "F" if self.imperial else "C"
        
    def context(self, config):
        return f"The user is currently in {config['city']}, {config['country']}."

    def _get_weather(self, city, state_code=None, country_code=None):
        """Gets the current weather in a given city."""
        location = city
        if state_code:
            location +=f",{state_code}"
        if country_code:
            location +=f",{country_code}"
        observation = self.mgr.weather_at_place(location)
        return observation.weather

    def _get_weather_description(self, weather):
        weather_variables = []

        # Sky
        weather_variables.append(f"Sky: {weather.detailed_status}")
        weather_variables.append(f"Sunrise: {self.__format_time(weather.srise_time)}")
        weather_variables.append(f"Sunset: {self.__format_time(weather.sset_time)}")

        # Rain

        if weather.rain != {}:
            weather_variables.append("Rain: True")
        if weather.snow != {}:
            weather_variables.append("Snow: True")
        weather_variables.append(f"Humidity: {weather.humidity}")

        # Temperatures
        temperatures = [weather.temp['temp'], weather.temp['temp_max'], weather.temp['temp_min']]
        if self.imperial:
            temperatures = [round(self.__to_fahrenheit(temp)) for temp in temperatures]
        else:
            temperatures = [round(self.__to_celcius(temp)) for temp in temperatures]
        weather_variables.append(f"High Temperature: {temperatures[1]}{self.symbol}")
        weather_variables.append(f"Low Temperature: {temperatures[2]}{self.symbol}")
        weather_variables.append(f"Current Temperature: {temperatures[0]}{self.symbol}")
        weather_variables.append(f"Feels like: {temperatures[0]}{self.symbol}")

        # Winds
        wind_speed = weather.wnd['speed']
        if self.imperial:
            wind_speed = self.__to_miles(wind_speed)
        weather_variables.append(f"Wind Speed: {wind_speed}")

        return weather_variables

    def __format_time(self, timestamp):
        dt = datetime.fromtimestamp(timestamp, self.timezone)
        return dt.strftime("%I:%M %p")

    def __to_miles(self, kilometers):
        return kilometers * 1.61

    def __to_fahrenheit(self, kelvin):
        return kelvin * 9/5 - 459.67

    def __to_celcius(self, kelvin):
        return kelvin - 273.15

    def get_weather(self, city, state_code=None, country_code=None):
        """Gets various weather information including temperature, rain, humidity, wind, etc."""

        # Get information about the weather
        weather = self._get_weather(city, state_code, country_code)

        # Form the next prompt
        prompt = self.interface.context[-1]['content'][0]['text']
        prompt += "\n\nYou've already called get_weather, use the below information to reply to this prompt."
        prompt += "\n\nBelow is a list of attributes about the weather which can help answer the previous prompt."

        weather_description = self._get_weather_description(weather)
        for var in weather_description:
            prompt+=f"\n{var}"

        message = self.functions['prompt'](prompt)
        if message:
            message = message.replace("°C", " degrees celcius")
            message = message.replace("°F", " degrees fahrenheit")
            message = message.replace("km/h", "kilometers per hour")
            message = message.replace("mph", " miles per hour")
            self.functions['say'](message)
    get_weather.variables={"city": "The name of the city to get the weather from.", "state_code": "The ISO 3166 state code for the city.", "country_code": "The ISO 3166 country code for the country the city is in."}
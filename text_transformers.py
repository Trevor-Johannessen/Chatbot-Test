class TextTransformer():
    @staticmethod
    def units(message):
        message = message.replace("°C", " degrees celcius")
        message = message.replace("°F", " degrees fahrenheit")
        message = message.replace("km/h", "kilometers per hour")
        message = message.replace("mph", " miles per hour")
        return message
    
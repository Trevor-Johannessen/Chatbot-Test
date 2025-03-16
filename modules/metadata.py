from datetime import datetime

class Metadata():
    def __init__(self, config):
        pass

    def _context(self, config):
        additional_context = 'Below are some fun facts you might find useful.\n'
        additional_context += "You are in version 0.0.3.\n"
        additional_context += "You were first created on February 17th, 2025 (You can consider this a birthday).\n"
        additional_context += f"The date is {datetime.now().strftime('%A, %B %d, %Y')}\n"
        return additional_context
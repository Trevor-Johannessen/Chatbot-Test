import requests

class Media():
    def __init__(self, config):
        self.interface = config['interface']

    def change_volume(self, direction: str, delta: int = 1):
        """Changes the volume of output audio."""
        print(f"Direction = {direction}, Delta = {delta}")
        self.interface.clear_recent_context()
        if direction.lower() == "decrease":
            endpoint = "volumedown"
        elif direction.lower() == "increase":
            endpoint = "volumeup"
        else:
            self.interface.say_canned("bad_volume_direction")
        try:
            response = requests.get(f"http://192.168.1.102:8000/{endpoint}?magnitude={delta}")
            if response.status_code != 200:
                raise Exception("")
        except requests.exceptions.RequestException as e:
            self.interface.say_canned("volume_change_fail")
    change_volume.variables={"delta":"The amount to change the volume by.", "direction":"Direction of the volume. Should use the words 'increase' or 'decrease'."}

    def next_song(self):
        """Skips to the next song in the queue."""
        try:
            self.interface.clear_recent_context()
            response = requests.get(f"http://192.168.1.102:8000/music/next")
            if response.status_code != 200:
                raise Exception("")
        except requests.exceptions.RequestException as e:
            self.interface.say_canned("cant_skip_song")

    def prev_song(self):
        """Skips to the previous song in the queue."""
        try:
            self.interface.clear_recent_context()
            response = requests.get(f"http://192.168.1.102:8000/music/prev")
            if response.status_code != 200:
                raise Exception("")
        except requests.exceptions.RequestException as e:
            self.interface.say_canned("cant_skip_song")

    def toggle_song(self):
        """Pauses or plays the current song."""
        try:
            self.interface.clear_recent_context()
            response = requests.get("http://192.168.1.102:8000/music/pause")
            if response.status_code != 200:
                raise Exception("")
        except requests.exceptions.RequestException as e:
            self.interface.say(f"Could not skip song.")
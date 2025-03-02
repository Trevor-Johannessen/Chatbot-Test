import requests
import os

class Media():
    def __init__(self, config):
        self.interface = config['interface']
        self.api_key = os.environ['SPOTIFY_API_KEY']

    def change_volume(self, direction: str, delta: int = 1):
        pass

    def next_song(self):
        """Skips to the next song in the queue."""
        pass

    def prev_song(self):
        """Skips to the previous song in the queue."""
        pass

    def toggle_song(self):
        """Pauses or plays the current song."""
        pass
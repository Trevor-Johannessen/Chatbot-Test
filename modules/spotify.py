import requests
from spotipy import Spotipy
from spotipy.oauth2 import SpotifyOAuth

import os

class Media():
    def __init__(self, config):
        self.interface = config['interface']
        self.client_id = os.environ['SPOTIFY_CLIENT_ID']
        self.client_secret = os.environ['SPOTIFY_CLIENT_SECRET']
        self.redirect_uri = os.environ['SPOTIFY_REDIRECT_URI']
        self.scopes = config['spotify_scopes']
        self.client = Spotipy(auth_manager=SpotifyOAuth(scope=self.scopes))

    def change_volume(self, direction: str, delta: int = 1):
        pass

    def next_song(self):
        """Skips to the next song in the queue."""
        pass

    def prev_song(self):
        """Skips to the previous song in the queue."""
        pass

    def pause_song(self):
        """Pauses or plays the current song."""
        pass

    def add_current_song_to_library(self):
        """Adds the currently playing song to the user's library."""
        pass
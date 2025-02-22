from mcstatus import JavaServer
import os
import requests

class Minecraft():
    def __init__(self, config):
        self.server_address = config["minecraft_server_addr"]
        self.api_address = config["minecraft_api_addr"]
        self.server = JavaServer.lookup(self.server_address)

    def minecraft_kick_player(self, player: str = None, reason: str = ""): # should make this an enum for the function I want
        """Kicks a player off the minecraft server."""
        try:
            if not player:
                raise Exception("specify_player")
            player=player.replace(" ", "")
            response = requests.get(f"http://{self.api_address}/minecraft/kick?player={player}&reason={reason}")
            if response.status_code != 200:
                raise Exception("kick_failed")
            self.interface.say(f"Kicked {player}.")
        except Exception as e:
            self.interface.say_canned(e)
    minecraft_kick_player.variables={"player":"The player to kick.", "reason":"A message explaining why the player was kicked."}

    def minecraft_ban_player(self, player: str = None, reason: str = ""): # should make this an enum for the function I want
        """Bans a player from the minecraft server."""
        try:
            if not player:
                raise Exception("specify_player")
            phonetic_name=player 
            player=player.replace(" ", "")
            response = requests.get(f"http://{self.api_address}/minecraft/ban?player={player}&reason={reason}")
            if response.status_code != 200:
                raise Exception("ban_failed")
            self.interface.say(f"Banned {phonetic_name}.")
        except Exception as e:
            self.interface.say_canned(e)
    minecraft_ban_player.variables={"player":"The player to ban.", "reason":"A message explaining why the player was banned."}

    def minecraft_pardon_player(self, player: str = None): # should make this an enum for the function I want
        """Pardons (unbans) a player on the minecraft server."""
        try:
            if not player:
                raise Exception("specify_player")
            phonetic_name=player 
            player=player.replace(" ", "")
            response = requests.get(f"http://{self.api_address}/minecraft/pardon?player={player}")
            if response.status_code != 200:
                raise Exception("pardon_failed")
            self.interface.say(f"Unbanned {phonetic_name}.")
        except Exception as e:
            self.interface.say_canned(e)
    minecraft_pardon_player.variables={"player":"The player to pardon."}

    def minecraft_mute_player(self, player: str = None): # should make this an enum for the function I want
        """Mutes a player on the minecraft server."""
        try:
            if not player:
                raise Exception("specify_player")
            phonetic_name=player
            player=player.replace(" ", "")
            response = requests.get(f"http://{self.api_address}/minecraft/mute?player={player}")
            if response.status_code != 200:
                raise Exception("mute_failed")
            self.interface.say(f"Muted {phonetic_name}.")
        except Exception as e:
            self.interface.say_canned(e)
    minecraft_mute_player.variables={"player":"The player to mute."}

    def minecraft_unmute_player(self, player: str = None): # should make this an enum for the function I want
        """Unmutes a player on the minecraft server."""
        try:
            if not player:
                raise Exception("specify_player")
            phonetic_name=player 
            player=player.replace(" ", "")
            response = requests.get(f"http://{self.api_address}/minecraft/unmute?player={player}")
            if response.status_code != 200:
                raise Exception("failed_unmute")
            self.interface.say(f"Unmuted {phonetic_name}.")
        except Exception as e:
            self.interface.say_canned(e)
    minecraft_unmute_player.variables={"player":"The player to unmute."}

    def minecraft_send_message(self, message: str = None): # should make this an enum for the function I want
        """Sends a message to the minecraft server."""
        try:
            if not message:
                raise Exception("specify_message")
            response = requests.get(f"http://{self.api_address}/minecraft/say?message={message}")
            if response.status_code != 200:
                raise Exception("message_failed")
            self.interface.say_canned(f"message_sent")
        except Exception as e:
            self.interface.say(e)
    minecraft_send_message={"message":"The message to send."}

    def get_minecraft_status(self, list_players: bool = False): # should make this an enum for the function I want
        """Gets the number of players or list of players currently on my minecraft server."""
        server = JavaServer.lookup("mc.sector-alpha.net")
        response = ""
        try:
            status = server.status()
            player_count = status.players.online
            player_list = [player.name for player in status.players.sample] if status.players.sample else []
            if status.players.online == 0:
                self.interface.say_canned("nobody_online")
                return
            elif list_players and player_count == 1:
                response = f"{player_list[0]} is currently online."
            elif list_players:
                response = ",\n".join(player_list) + " are currently online."
            elif player_count == 1:
                response = f"There is currently {player_count} person online."
            else:
                response = f"There are currently {player_count} people online."
            self.interface.say(response)
        except Exception as e:
            print(e)
            self.interface.say_canned("server_offline")
    get_minecraft_status.variables={"list_players":"Respond with a list of online players instead of a number."}
import json
from pydantic import BaseModel

class BaseMessages(BaseModel):
    pass

class LobbyMessages(BaseMessages):
    """Generic messages for lobby"""
    game_name: str
    name: str

    def join_message(self):
        return f"{self.game_name} joined to game {self.name}"
    
    def left_message(self):
        return f"{self.game_name} left game {self.name}"
    
    def start_message(self):
        return f"game {self.game_name} started"


class InGameMessages(BaseMessages):
    """Generic messages for game"""
    player_name: str
    player_target: str | None = None
    card: str

    def card_played(self):
        return f"{self.player_name} played {self.card}"
    
    def targeted_card_played(self):
        return f"{self.player_name} played {self.card} over {self.player_target}"
    
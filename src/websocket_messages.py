import json
from pydantic import BaseModel

class BaseMessages(BaseModel):
    pass

class LobbyMessages(BaseMessages):
    """Generic messages for lobby"""
    player_name: str | None = None
    game_name: str

    def join_message(self):
        return f"{self.player_name} joined to game {self.game_name}"
    
    def left_message(self):
        return f"{self.player_name} left game {self.game_name}"
    
    def start_message(self):
        return f"game {self.game_name} started"


class InGameMessages(BaseMessages):
    """Generic messages for game"""
    player_name: str
    player_target: str | None = None
    card: str | None = None

    def card_played(self):
        return f"{self.player_name} played {self.card}"
    
    def targeted_card_played(self):
        return f"{self.player_name} played {self.card} over {self.player_target}"
    
    def drawed_card(self):
        return f"{self.player_name} drawed a card"
    
    def new_turn(self):
        return f"{self.player_name}'s turn"
    
    def exchange(self):
        return f"{self.player_name} exchanged card with {self.player_target}"
    
    def discard(self):
        return f"{self.player_name} discarded a card"
    
    def game_over(self):
        return f"game {self.game_name} is over"
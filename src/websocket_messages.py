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
    
    def start_message(self):
        return f"game {self.game_name} started"
    
    def host_leave(self):
        return f"game cancel, host left the game"
    

class GameEvents(BaseMessages):
    player_name: str
    player_target: str | None = None
    card: str | None = None
    event: str

    def draw_card(self):
        envent_type = "draw_card"
        return json.dumps({"event": envent_type, "player_name": self.player_name})
    
    def play_card(self):
        envent_type = "play_card"
        return json.dumps({"event": envent_type, "player_name": self.player_name})
    
    def exchange_card(self):
        envent_type = "exchange_card"
        return json.dumps({"event": envent_type, "player_name": self.player_name})
    
    def invite_exchange(self):
        envent_type = "invite_exchange"
        return json.dumps({"event": envent_type, "player_name": self.player_name})
    
    def wait(self):
        envent_type = "wait"
        return json.dumps({"event": envent_type, "player_name": self.player_name})
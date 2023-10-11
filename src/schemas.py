from pydantic import BaseModel
from typing import List, Optional

class CreateGameIn(BaseModel):
    """Create game form"""
    game_name: str
    player_name: str
    min_players: int
    max_players: int
    password: str | None = None

class CreateGameResponse(BaseModel):
    """Game creation response"""
    id: int
    host_id: int

class GameOut(BaseModel):
    """Outbound game"""
    id: int
    name: str
    min_players: int
    max_players: int
    password: str | None = None
    number_of_players: int

class GameProgress(BaseModel):
    """Game progress information"""
    is_over: bool
    in_turn: int

class PlayerIn(BaseModel):
    """Inbound player"""
    player_name: str
    password: str | None = None

class PlayerResponse(BaseModel):
    """Player creation response"""
    id: int

class PlayerOut(BaseModel):
    """Outbound player"""
    id: int
    game_id: str
    player_name: str

class PlayerInDB(BaseModel):
    """Player in database"""
    player_id: int
    name: str
    game_id: int
    postition: int
    role: str
    is_dead: bool
    in_lockdown: bool
    left_barrier: bool
    right_barrier: bool

class GameInDB(BaseModel):
    """Game in database"""
    game_id: int
    name: str
    host: int
    current_turn: int
    players: List[PlayerInDB]
    in_game: bool
    is_done: bool
    password: str
    going_clockwise: bool
    min_players: int
    max_players: int
    number_of_players: int

class CardOut(BaseModel):
    """Card information"""
    id: int
    name: str
    description: str
    kind: str
    playable: bool
    players: List[PlayerInDB] | None = None
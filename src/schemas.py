from pydantic import BaseModel

# Create Game Form
class CreateGameIn(BaseModel):
    """Create game form"""
    game_name: str
    player_name: str
    min_players: int
    max_players: int
    password: str | None = None

# Game creation response
class CreateGameResponse(BaseModel):
    """Game creation response"""
    id: int
    host_id: int

# Outbound game
class GameOut(BaseModel):
    """Outbound game"""
    id: int
    min_players: int
    max_players: int
    password: str | None = None
    number_of_players: int

# Inbound player
class PlayerIn(BaseModel):
    """Inbound player"""
    player_name: str
    password: str | None = None

# Player creation response
class PlayerResponse(BaseModel):
    """Player creation response"""
    id: int

# Outbound player
class PlayerOut(BaseModel):
    """Outbound player"""
    id: int
    game_id: str
    player_name: str



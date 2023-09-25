from pydantic import BaseModel

# Create Game Form
class CreateGameIn(BaseModel):
    game_name: str
    player_name: str
    min_players: int
    max_players: int
    password: str | None = None

# Game creation response
class CreateGameResponse(BaseModel):
    id: int
    host_id: int

# Outbound game
class GameOut(BaseModel):
    id: int
    min_players: int
    max_players: int
    password: str | None = None

# Inbound player
class PlayerIn(BaseModel):
    player_name: str
    game_id: str
    password: str | None = None

# Player creation response
class PlayerResponse(BaseModel):
    id: int

# Outbound player
class PlayerOut(BaseModel):
    id: int
    game_id: str
    player_name: str



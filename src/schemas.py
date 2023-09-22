from pydantic import BaseModel

# Create Game Form
class CreateGameIn(BaseModel):
    """Create a new game form"""
    game_name: str
    player_name: str
    min_players: int
    max_players: int
    password: str | None = None

class GamesInfoOut(BaseModel):
    """Response game information"""
    game_name: str
    min_players: int
    max_players: int

class GameInDB(BaseModel):
    """Response game information"""
    game_id: int
    game_name: str
    host_id: int
    min_players: int
    max_players: int
    password: str | None = None

class PlayerInDB(BaseModel):
    user_id: int
    game_id: int
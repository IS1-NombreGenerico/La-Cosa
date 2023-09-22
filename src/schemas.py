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

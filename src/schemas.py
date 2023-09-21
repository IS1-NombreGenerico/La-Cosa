from pydantic import BaseModel

# Create Game Form
class CreateGameIn(BaseModel):
    game_name: str
    player_name: str
    min_players: int
    max_players: int
    password: str | None = None


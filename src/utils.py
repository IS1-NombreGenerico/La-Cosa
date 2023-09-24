from entities import Game, Player
from schemas import GameOut, PlayerOut

def db_player_2_player_out(db_player: Player) -> PlayerOut:

    return PlayerOut(
        id=db_player.id,
        game_id=db_player.game_id,
        player_name=db_player.name,
    )

def db_game_2_game_out(db_game: Game) -> GameOut:

    return GameOut(
        id=db_game.id,
        min_players=db_game.min_players,
        max_players=db_game.max_players,
        password=db_game.password,
    )
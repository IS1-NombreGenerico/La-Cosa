from entities import Game, Player
from schemas import GameOut, PlayerOut, GameInDB, PlayerInDB
from typing import List

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
        number_of_players=db_game.number_of_players,
    )

def db_game_2_game_schema(db_game: Game, players) -> GameInDB:
    
        return GameInDB(
            game_id=db_game.id,
            name=db_game.name,
            host=db_game.host.id,
            current_turn=db_game.current_turn,
            in_game=db_game.in_game,
            players=players,
            is_done=db_game.is_done,
            password=db_game.password,
            going_clockwise=db_game.going_clockwise,
            min_players=db_game.min_players,
            max_players=db_game.max_players,
            number_of_players=db_game.number_of_players
        )

def db_player_2_player_schema(db_player: Player) -> PlayerInDB:
    
    return PlayerInDB(
        player_id=db_player.id, 
        name=db_player.name, 
        postition=db_player.position, 
        role=db_player.role, 
        is_dead=db_player.is_dead, 
        in_lockdown=db_player.in_lockdown, 
        left_barrier=db_player.left_barrier, 
        right_barrier=db_player.right_barrier)
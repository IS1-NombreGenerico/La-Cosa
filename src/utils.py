from entities import Game, Player, Card
from schemas import GameOut, PlayerOut, GameInDB, PlayerInDB
from enumerations import CardName, Kind
from fastapi import HTTPException
from pony.orm import select
from typing import List
import random

def db_player_2_player_out(db_player: Player) -> PlayerOut:
    """Converts a Player object from the database to a PlayerOut object"""
    return PlayerOut(
        id=db_player.id,
        game_id=db_player.game_id,
        player_name=db_player.name,
    )

def db_game_2_game_out(db_game: Game) -> GameOut:
    """Converts a Game object from the database to a GameOut object"""
    return GameOut(
        id=db_game.id,
        name=db_game.name,
        min_players=db_game.min_players,
        max_players=db_game.max_players,
        password=db_game.password,
        number_of_players=db_game.number_of_players,
    )

def db_game_2_game_schema(db_game: Game, players) -> GameInDB:
    """Converts a Game object from the database to a GameInDB object"""
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
    """Converts a Player object from the database to a PlayerInDB object"""
    return PlayerInDB(
        player_id=db_player.id, 
        name=db_player.name, 
        game_id=db_player.game.id,
        postition=db_player.position, 
        role=db_player.role, 
        is_dead=db_player.is_dead, 
        in_lockdown=db_player.in_lockdown, 
        left_barrier=db_player.left_barrier, 
        right_barrier=db_player.right_barrier)


def validate_game(id_game: int) -> Game:
    """Verifies that a game exists in the database"""
    game = select(p for p in Game if p.id == id_game).first()
    if game is None:
        raise HTTPException(status_code=404, detail="INVALID_GAME")
    return game

def validate_player(id_player: int) -> Player:
    """Verifies if a player exists in the database"""
    player = select(p for p in Player if p.id == id_player).first()
    if player is None:
        raise HTTPException(status_code=404, detail="INVALID_PLAYER")
    return player

def shuffle_and_assign_positions(players) -> List[Player]:
    """Shuffles the players and assigns them a position"""
    players_list = list(players)
    random.shuffle(players_list)
    
    for num, player in enumerate(players_list, start=1):
        player.position = num
        
    return players_list

kind_list = [Kind.THETHING, Kind.INFECTION, Kind.ACTION, Kind.ACTION, Kind.ACTION, 
             Kind.ACTION, Kind.ACTION, Kind.ACTION, Kind.ACTION, Kind.ACTION, 
             Kind.OBSTACLE, Kind.ACTION, Kind.DEFENSE, Kind.DEFENSE, Kind.DEFENSE, 
             Kind.DEFENSE, Kind.DEFENSE, Kind.OBSTACLE, Kind.PANIC, Kind.PANIC, 
             Kind.PANIC, Kind.PANIC, Kind.PANIC, Kind.PANIC, Kind.PANIC, 
             Kind.PANIC, Kind.PANIC, Kind.PANIC, Kind.PANIC, Kind.PANIC]

def get_card_deck(num_of_players : int):
    """Returns the list of the amount of each card given the number of players"""
    card_deck_mapping = {
        4: [1, 8, 2, 0, 1, 4, 2, 1, 2, 1, 2, 1, 2, 10, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0],
        5: [1, 8, 2, 0, 1, 4, 2, 1, 2, 1, 2, 1, 2, 10, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0],
        6: [1, 8, 2, 0, 1, 4, 2, 1, 2, 1, 2, 1, 2, 10, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0],
        7: [1, 8, 2, 0, 1, 4, 2, 1, 2, 1, 2, 1, 2, 10, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0],
        8: [1, 8, 2, 0, 1, 4, 2, 1, 2, 1, 2, 1, 2, 10, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0],
        9: [1, 8, 2, 0, 1, 4, 2, 1, 2, 1, 2, 1, 2, 10, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0],
        10: [1, 8, 2, 0, 1, 4, 2, 1, 2, 1, 2, 1, 2, 10, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0],
        11: [1, 8, 2, 0, 1, 4, 2, 1, 2, 1, 2, 1, 2, 10, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0],
        12: [1, 8, 2, 0, 1, 4, 2, 1, 2, 1, 2, 1, 2, 10, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0],
    }
    
    return card_deck_mapping[num_of_players]

def create_deck(id_game : int):
    """Creates a deck given an amount of players"""
    game = validate_game(id_game)

    list_deck = get_card_deck(game.number_of_players)

    for card, cantidad, kind in zip(CardName, list_deck, kind_list):
        for i in range(cantidad):
            c = Card(
                name = card, 
                kind = kind,
                game = game,
            )

def validate_card(id_card: int, id_player: int ) -> bool:
    """Validate if the card is in the player's hand and can be played"""
    player = validate_player(id_player)
    return id_card in [card.id for card in player.hand]

def play_card_with_target(game: Game, id_card: int, id_player: int) -> bool:
    """Plays a card with a target and returns success/failure"""
    card = select(c for c in Card if c.id == id_card).first()
    match card.name:
        case CardName.FLAMETHROWER:
            return True
        case _:
            return False
from entities import Game, Player, Card
from enumerations import Role
from pony.orm import db_session, flush
from fastapi import HTTPException, status
from schemas import GameOut, GameProgress, PlayerId, CardId, CardOut
from pony.orm import select
from utils import validate_game, validate_player, validate_card, db_game_2_game_progress, db_card_2_card_out, game_data_sample
from typing import List
import websocket_messages
from connection_manager import ConnectionManager

def valid_turn(db_player: Player) -> bool:
    """Returns if the player it's in turn"""
    return db_player.position == db_player.game.current_turn

def valid_next_turn(db_player: Player) -> bool:
    """Returns if the player it's in turn"""
    return db_player.position == (db_player.game.current_turn + 1 % db_player.game.number_of_players)

def get_indexes(db_game: Game) -> list:
    """Returns the indexes of the players in the game"""
    indexes = select(
        {
            "id": p.id,
            "turn": p.position
        }
        for p in Game.players)
    
    return indexes

def get_current_player(db_game: Game) -> Player:
    """Returns the current player"""
    db_player = select(p for p in Game.players if p.position == db_game.current_turn and p.is_dead == False).first()
    
    return db_player.id

def get_winners(game: Game) -> dict:
    """Returns the winners of the game"""
    live_players = [p for p in game.players if not p.is_dead]
    human_players = [p for p in live_players if p.role == "HUMAN"]
    infected_players = [p for p in live_players if p.role in ["INFECTED", "THE THING"]]
    
    if human_players:
        return {"winners" : PlayerId(human_players),
            "winningTeam" :"Humans"}
    elif len(live_players) == game.number_of_players:
        thing_player = next((p for p in live_players if p.role == "THE THING"), None)
        return {"winners" : PlayerId(thing_player),
            "winningTeam" : "The Thing"}
    else:
        return {"winners" : PlayerId(infected_players),
            "winningTeam" : "The Thing and Infecteds"}

def finish_game(db_game: Game) -> dict:
    """Finishes the game and returns the winners"""
    with db_session:
        if(db_game.in_game):
            db_game.in_game = False
            response = get_winners(game)
            
            players_of_game = Player.select(lambda p: p.game.id == db_game.id)
            for player in players_of_game:
                player.delete()
            
            cards_of_game = Card.select(lambda c: c.game.id == db_game.id)
            for card in cards_of_game:
                card.delete()
            
            return response
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_ACTION"
            )

def game_is_over(db_game) -> bool:
    """Returns if the game is over"""
    db_game = validate_game(db_game)
    uninfected_players = select(p for p in Player if not p.is_dead and p.role == Role.HUMAN)
    
    return len(uninfected_players) == 0 or not game.in_game

def retrieve_information(id_game: int, id_player:int, id_card: int) -> CardOut:
    """Returns information about a card
    Input: 
    ---------
    Output: CardOut
        Information about the card
    """
    with db_session:
        game = utils.validate_game(id_game)
        player = utils.validate_player(id_player)
        card = utils.validate_card(id_card, id_player)

        return utils.db_card_2_card_out(card, player)

async def discard_card(id_game: int, id_player:int, id_card: int) -> bool:
    """Discards a card from the player's hand"""
    with db_session:
        game = utils.validate_game(id_game)
        player = utils.validate_player(id_player)
        card = utils.validate_card(id_card, id_player)
        utils.discard_card(game, player, card)
        flush()
        await connection_manager.send_lobby_info(id_game, utils.game_data_sample(game))
        await connection_manager.broadcast(game.id, websocket_messages.InGameMessages(player_name=player.name, card=card.name).discard())
    return True

async def exchange_card(id_game: int, id_player:int, id_card: int, id_card2: int) -> GameProgress:
    """Exchange a card with a player based in the direction of turn"""
    #Se deberia checker desde el front que no sean jugadores muertos
    with db_session:
        game = utils.validate_game(id_game)
        player1 = utils.validate_player(id_player)
        player2 = utils.validate_player(game.players[player1.position + 1 % game.number_of_players].id if game.going_clockwise 
                                    else game.players[player1.position - 1 % game.number_of_players].id)
        card1 = utils.validate_card(id_card, id_player)
        card2 = utils.validate_card(id_card2, player2.id)
        utils.exchange_card(game, player1, player2, card1, card2)
        flush()
        await connection_manager.send_lobby_info(id_game, utils.game_data_sample(game))
        await connection_manager.broadcast(game.id,websocket_messages.InGameMessages(player_name=player1.name, 
                                                                                    player_target=player2.name, card=card1.name).exchange())
    return utils.db_game_2_game_progress(game)



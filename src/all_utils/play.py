from entities import Game, Player, Card
from schemas import GameOut, GameProgress, PlayerId, CardId, CardOut
from enumerations import CardName, Kind
from pony.orm import db_session, flush, select
from fastapi import HTTPException, status
from utils import validate_game, validate_player, validate_card, db_game_2_game_progress, db_card_2_card_out, game_data_sample
from typing import List
import websocket_messages
from connection_manager import ConnectionManager

def implemented_card(card: Card) -> bool:
    """Return if a action card is implemented"""
    return ((card.name == CardName.FLAMETHROWER) or
        (card.name == CardName.ANALYSIS) or
        (card.name == CardName.AXE) or
        (card.name == CardName.SUSPICION) or
        (card.name == CardName.WHISKY) or
        (card.name == CardName.SWAP_PLACES) or
        (card.name == CardName.WATCH_YOUR_BACK) or
        (card.name == CardName.SEDUCTION) or
        (card.name == CardName.YOU_BETTER_RUN))

async def play_card_announce(game: Game, player_afected: Player, card: Card):
    """Announces the play of a card"""
    await connection_manager.broadcast(game.id, 
        websocket_messages.InGameMessages(player_name=card.player.name,
                                          player_target=player_afected.name,
                                          card=card.name).targeted_card_played())

async def play_card(game: Game, card: Card, player_afected: Player) -> GameProgress:
    """Plays a card"""

    player_afected = utils.validate_player(id_player_afected)
    match card.name: 
        case CardName.FLAMETHROWER:
            play_card_announce(game, player_afected, card)
            play_card.play_flamethrower(card, player_afected)
            
        case CardName.WATCH_YOUR_BACK:
            play_card.play_watch_your_back(game, card)
            await connection_manager.broadcast(game.id,
                websocket_messages.InGameMessages(player_name=player.name, card=card.name).card_played())
        case CardName.SWAP_PLACES:
            play_card.play_swap_places(card, player, player_afected)
            play_card_announce(game, player_afected, card)

        case CardName.YOU_BETTER_RUN:
            play_card.play_you_better_run(card, player_afected)
            play_card_announce(game, player_afected, card)

        case CardName.SEDUCTION:
            play_card.play_seduction(card, player_afected)
            play_card_announce(game, player_afected, card)

        case CardName.ANALYSIS:
            play_card.play_analysis(card, player_afected)
            play_card_announce(game, player_afected, card)

        case CardName.AXE:
            play_card.play_axe(card, player_afected)
            play_card_announce(game, player_afected, card)

        case CardName.SUSPICION:
            play_card.play_suspicion(card, player_afected)
            play_card_announce(game, player_afected, card)

        case CardName.WHISKY:
            play_card.play_whisky(card)
            await connection_manager.broadcast(game.id,
                websocket_messages.InGameMessages(player_name=player.name, card=card.name).card_played())

        case _:
            await connection_manager.broadcast(game.id,
                websocket_messages.InGameMessages(player_name=player.name, card=card.name).card_played() + " (NOT IMPLEMENTED)")
    
    flush()
    await connection_manager.send_lobby_info(id_game, utils.game_data_sample(game))
    return utils.db_game_2_game_progress(game)

def play_flamethrower(game: Game, player_afected: Player) -> None:
    """Plays the flamethrower card"""
    
    player_afected.is_dead = True

    for c in player_afected.hand:
        game.discarded.add(c)
    player_afected.hand.clear()

    for p in game.players:
        if p.position > player_afected.position:
            p.position -= 1

def play_watch_your_back(game: Game) -> None:
    """Play the watch your back card"""
    game.going_clockwise = not game.going_clockwise

def play_swap_places(player: Player, player_afected: Player) -> None:
    """Play all the place swap cards"""
    player.position, player_afected.position = player_afected.position, player.position

def play_change_cards(player: Player, player_afected: Player) -> None:
    """Play all the card exchange cards"""
    pass

def play_remove_obstacle(player_afected: Player) -> None:
    """Plays all the remove obstacle card"""
    # player_afected.in_lockdown = False
    # player_afected.left_barrier = False
    # player_afected.right_barrier = False
    pass

def play_suspicion(player_afected: Player) -> None:
    pass

def play_whisky() -> None:
    pass

def play_analysis() -> None:
    pass
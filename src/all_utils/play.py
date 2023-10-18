from entities import Game, Player, Card
from schemas import GameOut, GameProgress, PlayerId, CardId
from enumerations import CardName, Kind
from typing import List

def playable_card(db_card: Card, db_player: Player) -> bool:
    """Returns if the card is playable"""
    
    return db_card.player.id == db_player.id and db_card.kind == Kind.ACTION

def targeted_players(db_card: Card, db_player: Player) -> List[Player]:
    """Returns the players that can be targeted"""
    if playable_card(db_card, db_player) == False:
        return []
    
    match db_card.name:
        case CardName.FLAMETHROWER:
            return [
                    p
                    for p in db_player.game.players
                    if p.id != db_player.id and not p.is_dead and
                    (p.position == ((db_player.position + 1) % db_player.game.number_of_players) or
                    p.position == ((db_player.position - 1) % db_player.game.number_of_players))
                ]
        case CardName.SWAP_PLACES:
            return [
                    p
                    for p in db_player.game.players
                    if p.id != db_player.id and not p.in_lockdown and not p.is_dead and
                    (p.position == ((db_player.position + 1) % db_player.game.number_of_players and not p.left_barrier) or
                    p.position == ((db_player.position - 1) % db_player.game.number_of_players and not p.right_barrier))
                        
            ]
        case CardName.AXE:
            return [
                    p
                    for p in db_player.game.players
                    if not p.is_dead and (p.in_lockdown or p.left_barrier or p.right_barrier) and 
                    (p.position == db_player.position or
                    p.position == ((db_player.position + 1) % db_player.game.number_of_players) or
                    p.position == ((db_player.position - 1) % db_player.game.number_of_players))
            ]
        case CardName.SEDUCTION:
            return [
                    p
                    for p in db_player.game.players
                    if p.id != db_player.id and not p.in_lockdown and not p.is_dead
            ]
        case CardName.ANALYSIS:
            return [
                    p
                    for p in db_player.game.players
                    if p.id != db_player.id and not p.is_dead and
                    p.position == ((db_player.position + 1) % db_player.game.number_of_players) or
                    p.position == ((db_player.position - 1) % db_player.game.number_of_players)
                ]            
        case _:
            return []

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

async def play_card(card: CardId, player_afected: PlayerId) -> GameProgress:
    """Plays a card"""

    with db_session:
        player = utils.validate_player(card.player_id)
        game = utils.validate_game(player.game.id)
        card = utils.validate_card(card.id, card.player_id)

        if card.name == CardName.WATCH_YOUR_BACK:
            if not (id_player_afected is None):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="INVALID_PLAY"
                )
        else:
            player_afected = utils.validate_player(id_player_afected)

        if player.position != game.current_turn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="NOT_ON_TURN"
            )

        if card.kind != Kind.ACTION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_PLAY"
            )
        
        match card.name: 
            case CardName.FLAMETHROWER:
                play_card.play_flamethrower(card, player_afected)
                await connection_manager.broadcast(game.id, 
                                            websocket_messages.InGameMessages(player_name=player.name, player_target=player_afected.name, card=card.name)
                                            .targeted_card_played())
            case CardName.WATCH_YOUR_BACK:
                play_card.play_watch_your_back(game, card)
                await connection_manager.broadcast(game.id,
                                            websocket_messages.InGameMessages(player_name=player.name, card=card.name).card_played())
            case CardName.SWAP_PLACES:
                play_card.play_swap_places(card, player, player_afected)
                await connection_manager.broadcast(game.id, 
                                            websocket_messages.InGameMessages(player_name=player.name, player_target=player_afected.name, card=card.name)
                                            .targeted_card_played())
            case CardName.YOU_BETTER_RUN:
                play_card.play_you_better_run(card, player_afected)
                await connection_manager.broadcast(game.id, 
                                            websocket_messages.InGameMessages(player_name=player.name, player_target=player_afected.name, card=card.name)
                                            .targeted_card_played())
            case CardName.SEDUCTION:
                play_card.play_seduction(card, player_afected)
                await connection_manager.broadcast(game.id, 
                                            websocket_messages.InGameMessages(player_name=player.name, player_target=player_afected.name, card=card.name)
                                            .targeted_card_played())
            case CardName.ANALYSIS:
                play_card.play_analysis(card, player_afected)
                await connection_manager.broadcast(game.id, 
                                            websocket_messages.InGameMessages(player_name=player.name, player_target=player_afected.name, card=card.name)
                                            .targeted_card_played())
            case CardName.AXE:
                play_card.play_axe(card, player_afected)
                await connection_manager.broadcast(game.id, 
                                            websocket_messages.InGameMessages(player_name=player.name, player_target=player_afected.name, card=card.name)
                                            .targeted_card_played())
            case CardName.SUSPICION:
                play_card.play_suspicion(card, player_afected)
                await connection_manager.broadcast(game.id, 
                                            websocket_messages.InGameMessages(player_name=player.name, player_target=player_afected.name, card=card.name)
                                            .targeted_card_played())
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
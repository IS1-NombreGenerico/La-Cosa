from entities import Game, Player, Card
from enumerations import CardName, Kind
from typing import List, Tuple

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

def play_flamethrower(game: Game, player_afected: Player) -> None:
    """Plays the flamethrower card"""
    
    #Set dead status
    player_afected.is_dead = True
    #Discard his hand
    for c in player_afected.hand:
        game.discarded.add(c)
    player_afected.hand.clear()
    #Reorganize the positions
    living_players = [p for p in game.players if not p.is_dead]
    living_players.sort(key=lambda x: x.position)
    for (turn, player) in enumerate(living_players):
        if player.position == game.current_turn:
            game.current_turn = turn
        player.position = turn

def play_watch_your_back(game: Game) -> None:
    """Play the watch your back card"""
    game.going_clockwise = not game.going_clockwise

def play_swap_places(player: Player, player_afected: Player) -> dict:
    if player_afected.position == player.position + 1 and not player_afected.left_barrier:
        mensaje = swap_places(player, player_afected)
    elif player_afected.position == player.position - 1 and not player_afected.right_barrier:
        mensaje = swap_places(player, player_afected)
    return mensaje

def swap_places(player: Player, player_afected: Player) -> dict:
    """Play all the place swap cards"""
    if player_afected.in_lockdown:
        player.position, player_afected.position = player_afected.position, player.position
    return players_positions(player.game)

def show_cards_of_player(player: Player) -> dict:
    mensaje = hand_to_list(List(player.hand))
    return {"hand to player": mensaje}

def play_you_better_run(player: Player, player_afected: Player) -> dict:
    return swap_places(player, player_afected)

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

def hand_to_list(hand: List[Card]) -> List[Tuple[int, str]]:
    """Converts a list of cards to a list of tuple int, strings"""
    return [(c.id, c.name) for c in hand]

def players_positions(game: Game) -> List[Tuple[int, str]]:
    """Returns the positions of the players"""
    return [(p.position, p.name) for p in List(game.players)]

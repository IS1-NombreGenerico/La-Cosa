from entities import Game, Player, Card
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
                    if p.id != db_player.id and
                    p.turn == ((db_player.turn + 1) % db_player.game.number_of_players) or
                    p.turn == ((db_player.turn - 1) % db_player.game.number_of_players)
                ]
        case CardName.SWAP_PLACES:
            return [
                    p
                    for p in db_player.game.players
                    if p.id != db_player.id and 
                    p.in_lockdown == False and
                    p.left_barrier == False and 
                    p.right_barrier == False
            ]
        case CardName.AXE:
            return [
                    p
                    for p in db_player.game.players
                    if p.in_lockdown == True or 
                    p.left_barrier == True or 
                    p.right_barrier == True
            ]
        case CardName.SEDUCTION:
            return [
                    p
                    for p in db_player.game.players
                    if p.id != db_player.id and
                    p.in_lockdown == False
            ]
        case CardName.ANALYSIS:
            return [
                    p
                    for p in db_player.game.players
                    if p.id != db_player.id and
                    p.position == ((db_player.position + 1) % db_player.game.number_of_players) or
                    p.position == ((db_player.position - 1) % db_player.game.number_of_players)
                ]            
        case _:
            return []

def implemented_card(card: Card) -> bool:
    """Return if the card is implemented"""
    return card.name == CardName.FLAMETHROWER

def play_flamethrower(game: Game, player_afected: Player) -> None:
    """Plays the flamethrower card"""
    
    #Set dead status
    player_afected.is_dead = True
    #Discard his hand
    for c in player_afected.hand:
        game.discarded.add(c)
    player_afected.hand.clear()
    #Reorganize the positions
    for p in game.players:
        if p.position > player_afected.position:
            p.position -= 1

def play_watch_your_back(game: Game, card: Card) -> None:
    game.going_clockwise = not game.going_clockwise

def play_swap_places(card: Card, player: Player, player_afected: Player) -> None:
    player.position, player_afected.position = player_afected.position, player.position

def play_you_better_run(card: Card, player_afected: Player) -> None:
    pass

def play_seduction(card: Card, player_afected: Player) -> None:
    pass

def play_analysis(card: Card, player_afected: Player) -> None:
    pass

def play_axe(card: Card,  player_afected: Player) -> None:
    player_afected.in_lockdown = False
    player_afected.left_barrier = False
    player_afected.right_barrier = False

def play_suspicion(card: Card, player_afected: Player) -> None:
    pass

def play_whisky(card: Card) -> None:
    pass
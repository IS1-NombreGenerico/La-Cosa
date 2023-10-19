from entities import Game, Player, Card
from schemas import GameOut, PlayerOut, GameInDB, PlayerInDB, CardOut, GameProgress, PlayerId, CardId
from enumerations import CardName, Kind, Role
from fastapi import HTTPException
from pony.orm import select
from typing import List
import random

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

def db_player_2_player_out(db_player: Player) -> PlayerOut:
    """Converts a Player object from the database to a PlayerOut object"""
    return PlayerOut(
        id=db_player.id,
        game_id=db_player.game_id,
        player_name=db_player.name,
    )

def db_player_2_player_schemas(db_player: Player) -> PlayerInDB:
    """Converts a Player object from the database to a PlayerInDB object"""
    return PlayerInDB(
        player_id=db_player.id, 
        name=db_player.name, 
        game_id=db_player.game.id,
        postition=db_player.position, 
        role=db_player.role, 
        card=hand_to_list(db_player.hand),
        is_dead=db_player.is_dead, 
        in_lockdown=db_player.in_lockdown, 
        left_barrier=db_player.left_barrier, 
        right_barrier=db_player.right_barrier)

def db_player_2_player_id(db_player: Player) -> PlayerId:
    """Converts a Player object from the database to a PlayerId object"""
    return PlayerId(
        id=db_card.id,
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

def db_game_2_game_schema(db_game: Game, db_players = PlayerInDB) -> GameInDB:
    """Converts a Game object from the database to a GameInDB object"""
    return GameInDB(
            game_id=db_game.id,
            name=db_game.name,
            host=db_game.host.id,
            current_turn=db_game.current_turn,
            in_game=db_game.in_game,
            players=db_players,
            is_done=db_game.is_done,
            password=db_game.password,
            going_clockwise=db_game.going_clockwise,
            min_players=db_game.min_players,
            max_players=db_game.max_players,
            number_of_players=db_game.number_of_players
        )

def db_card_2_card_out(db_card: Card, db_player: Player) -> CardOut:
    """Converts a Card object from the database to a CardOut object"""
    return CardOut(
        id=db_card.id,
        name=db_card.name,
        description=db_card.description,
        kind=db_card.kind,
        playable=playable_card(db_card, db_player),
        players=targeted_players(db_card, db_player),
    )

def db_card_2_card_id(db_card: Card, db_player: Player) -> CardId:
    """Converts a Card object from the database to a CardId object"""
    return CardId(
        id=db_card.id,
        player=db_player.id,
    )

def db_game_2_game_progress(db_game: Game) -> GameProgress:
    """Converts a Game object from the database to a GameProgress object"""
    return GameProgress(
        is_over=db_game.is_done,
        next_turn=db_game.current_turn,
    )

def db_player_2_player_schema(db_player: Player) -> PlayerId:
    """Converts a Player object from the database to a PlayerId object"""
    return PlayerId(
        id=db_player.id,
    )

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

def validate_card(id_card: int, id_player: int) -> Card:
    """Verifies if the card exists in the database and is in the player's hand"""
    card = select(c for c in Card if c.id == id_card).first()
    if card is None:
        raise HTTPException(status_code=404, detail="INVALID_CARD")
    if card.player.id != id_player:
        raise HTTPException(status_code=404, detail="INVALID_PLAY")
    return card

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
        4: [1, 8, 3, 0, 1, 4, 4, 1, 2, 1, 2, 1, 2, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0],
        5: [1, 8, 3, 1, 1, 4, 4, 1, 2, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0],
        6: [1, 10, 3, 2, 1, 4, 5, 2, 2, 1, 3, 1, 2, 2, 2, 2, 2, 2, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0],
        7: [1, 12, 3, 2, 1, 5, 5, 2, 3, 1, 4, 2, 3, 2, 2, 2, 2, 2, 1, 1, 1, 2, 2, 2, 2, 2, 1, 2, 1, 1, 0],
        8: [1, 13, 3, 2, 1, 6, 5, 2, 3, 1, 5, 2, 3, 2, 3, 3, 2, 2, 1, 2, 1, 2, 2, 2, 2, 2, 1, 2, 1, 1, 0],
        9: [1, 15, 4, 3, 2, 7, 6, 2, 4, 2, 5, 2, 4, 2, 3, 3, 2, 2, 2, 2, 1, 2, 3, 3, 3, 3, 2, 3, 2, 2, 0],
        10: [1, 17, 4, 3, 2, 8, 7, 3, 4, 2, 6, 2, 4, 2, 3, 3, 2, 2, 2, 2, 1, 2, 3, 3, 3, 3, 2, 3, 2, 2, 1],
        11: [1, 20, 5, 3, 2, 8, 7, 3, 5, 2, 7, 3, 5, 3, 4, 4, 3, 3, 2, 2, 1, 2, 3, 3, 3, 3, 2, 3, 2, 2, 1],
        12: [1, 20, 5, 3, 2, 8, 7, 3, 5, 2, 7, 3, 5, 3, 4, 4, 3, 3, 2, 2, 1, 2, 3, 3, 3, 3, 2, 3, 2, 2, 1]
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
            )
            game.deck.add(c)

def draw_card(game: Game, player: Player) -> CardId:
    """Draws a card to the given player"""
    if(game.game_deck.is_empty()):
        for c in game.discarded:
            game.deck.add(c)
        game.discarded.clear()
    card = game.deck.random(1)
    player.hand.add(card)
    game.deck.remove(card)

    return db_card_2_card_id(card, player)

def playable_card(db_card: Card, db_player: Player) -> bool:
    """Returns if the card is playable"""
    
    return db_card.player.id == db_player.id and db_card.kind == Kind.ACTION

def discard_card(db_card: CardId):
    """Discards a card from the player's hand"""
    player = validate_player(db_card.player)
    card = validate_card(db_card.id, db_card.player)
    player.hand.remove(card)
    player.game.discarded.add(card)

def exchange_card(player1: Player, player2: Player, cardp1: Card, cardp2: Card) -> None:
    """Exchanges a card from player1 to player2"""
    
    if (cardp1.name == CardName.INFECTED and player1.role != Role.THING) or (cardp2.name == CardName.INFECTED and player2.role != Role.THING):
        raise HTTPException(status_code=404, detail="INVALID_EXCHANGE")
    elif (cardp1.name == CardName.INFECTED and player1.role == Role.THING and player2.role == Role.HUMAN):
        player2.role = Role.INFECTED
    elif (cardp2.name == CardName.INFECTED and player2.role == Role.THING and player1.role == Role.HUMAN):
        player1.role = Role.INFECTED

    player1.hand.remove(cardp1)
    player2.hand.remove(cardp2)
    player1.hand.add(cardp2)
    player2.hand.add(cardp1)

def hand_to_list(hand: List[Card]) -> List[str]:
    """Converts a list of cards to a list of strings"""
    return [card.name for card in hand]

def deal_cards(game_id: int):
    """Deal cards to players at the begin of the game and assign the role "the thing" to one of them"""
    game = validate_game(game_id)
    cards_set = set(game.deck)
    
    card_theThing = select(card for card in Card if card.name == "La Cosa" and card.game_deck == game).first()

    eligible_kinds = {"Acción", "Defensa"}
    cards_assigned = set()
    
    for player in game.players:
        for _ in range(4):
            valid_cards = [card for card in cards_set if card.kind in eligible_kinds and card not in cards_assigned]
            if valid_cards:
                card = random.choice(valid_cards)
                player.hand.add(card)
                cards_assigned.add(card)
                cards_set.discard(card)

    if game.players:
        theThingPlayer = random.choice(list(game.players))
    if theThingPlayer:
        card = random.choice(list(theThingPlayer.hand))
        cards_assigned.discard(card)
        theThingPlayer.hand.remove(card)
        theThingPlayer.hand.add(card_theThing)
        theThingPlayer.role = Role.THING

    for card in cards_assigned:
        game.deck.remove(card)

def obtain_games_available() -> list[GameOut]:
    try:
        filter_by_availability = lambda g: g.number_of_players < g.max_players and not g.in_game
        games = [
                    db_game_2_game_out(g)
                    for g in select(
                        g
                        for g in Game
                        if filter_by_availability(g)
                    )
                ]
    except: raise HTTPException(status_code=404, detail="UNABLE_TO_CONNECT_DATABASE")
    return games

def game_data_sample(game : Game) -> GameInDB:
    """Returns the data of a game"""
    players = [db_player_2_player_schemas(p) for p in game.players]
    return db_game_2_game_schema(game, players)
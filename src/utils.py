from entities import Game, Player, Card
from schemas import GameOut, PlayerOut, GameInDB, PlayerInDB, CardOut, GameProgress, PlayerId
from enumerations import CardName, Kind, Role
from fastapi import HTTPException
from pony.orm import select
from typing import List
from all_utils.play_card import playable_card, targeted_players
import random

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

def validate_card(id_card: int, id_player: int ) -> Card:
    """Validate if the card is in the player's hand and can be played"""
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

def draw_card(game: Game, player: Player) -> bool:
    """Draws a card to the given player"""
    if(game.game_deck.is_empty()):
        for c in game.discarded:
            game.deck.add(c)
        game.discarded.clear()
    card = game.deck.random(1)
    player.hand.add(card)
    game.deck.remove(card)
    return True

def get_winners(game: Game) -> dict:
    """Returns the winners of the game"""
    live_players = [p for p in game.players if not p.is_dead]
    human_players = [p for p in live_players if p.role == "HUMAN"]
    infected_players = [p for p in live_players if p.role in ["INFECTED", "THE THING"]]
    
    if human_players:
        return {"message" : "Humans Win",
            "winners" :db_player_2_player_schema(human_players)}
    elif len(live_players) == game.number_of_players:
        thing_player = next((p for p in live_players if p.role == "THE THING"), None)
        return {"message" : "Just the Thing Win",
            "winners" : db_player_2_player_schema([thing_player] if thing_player else [])}
    else:
        return {"message" : "The Thing and Infecteds Win",
            "winners" : db_player_2_player_schema(infected_players)}
    
def discard_card(game: Game, player: Player, card: Card) -> None:
    """Discards a card from the player's hand"""

    player.hand.remove(card)
    game.discarded.add(card)

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
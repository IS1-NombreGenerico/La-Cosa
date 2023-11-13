from pony.orm import (Database, PrimaryKey, Required, Set, Optional)
from enumerations import (Kind, Role, CardName)
import config

db = Database()

class Card(db.Entity):
    """Represent a Card in the database"""
    id = PrimaryKey(int, auto=True)
    name = Required(CardName, default=CardName.THE_THING)
    description = Required(str, default="description")
    kind = Required(Kind, default=Kind.ACTION)
    game_deck = Optional('Game', reverse="deck")
    game_discard = Optional('Game', reverse="discarded")
    player = Optional('Player', reverse="hand")
    required_players = Required(int, default=0)
    active_infection = Required(bool, default=False)
    revealed = Set('Player')

class Player(db.Entity):
    """Represent a Player in the database"""
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    host = Optional("Game", reverse="host", cascade_delete=True)
    game = Optional('Game')
    position = Required(int, default=0)
    role = Required(Role, default=Role.HUMAN)
    is_dead = Required(bool, default=False)
    hand = Set(Card)
    in_lockdown = Required(bool, default=False)
    left_barrier = Required(bool, default=False)
    right_barrier = Required(bool, default=False)
    exchange_offer = Required(int, default=-1) # Ponemos una de defensa si se requiere eso
    action = Required(int, default=-1) # Para settear la accion con un endpoint
    defense = Required(int, default=-1) # Para settear las defensas con un endpoint
    reveals = Set(Card)

class Game(db.Entity):
    """Represent a Game in the database"""
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    host = Required(Player, reverse="host")
    players = Set(Player)
    current_turn = Required(int, default=0)
    in_game = Required(bool, default=False)
    is_done = Required(bool, default=False)
    password = Optional(str)
    going_clockwise = Required(bool, default=True)
    min_players = Required(int, default=4, py_check=lambda x: x >= 4 and x <= 12)
    max_players = Required(int, default=12, py_check=lambda x: x >= 4 and x <= 12)
    deck = Set(Card)
    discarded = Set(Card)
    number_of_players = Required(int, default=1)
    turn_phase = Required(str, default="BEGIN") # TODO validate in schemas
    current_target = Required(int, default=-1) # TODO validate in schemas
    game_over_status = Required(Role, default="RUNNING")

db.bind(config.database, config.databasename, create_db=True)
db.generate_mapping(create_tables=True)

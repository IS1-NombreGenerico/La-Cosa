from pony.orm import (Database, PrimaryKey, Required, Set, Optional)
from enumerations import (Kind, Role, CardName)

db = Database()

class Card(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(CardName, default=CardName.THE_THING)
    description = Required(str, default="description")
    discarded = Required(bool, default=False)
    kind = Required(Kind, default=Kind.ACTION)
    game = Required('Game', reverse="deck")
    player = Required('Player', reverse="hand")
    required_players = Required(int, default=0)

class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    host = Optional("Game", reverse="host")
    game = Optional('Game')
    position = Required(int, default=0)
    role = Required(Role, default=Role.HUMAN)
    is_dead = Required(bool, default=False)
    hand = Set(Card)
    in_lockdown = Required(bool, default=False)
    left_barrier = Required(bool, default=False)
    right_barrier = Required(bool, default=False)

class Game(db.Entity):
    id = PrimaryKey(int, auto=True) 
    name = Required(str)
    host = Required(Player, reverse="host")
    players = Set(Player)
    current_turn = Required(int, default=0)
    in_game = Required(bool, default=False)
    is_done = Required(bool, default=False)
    password = Optional(str)
    going_clockwise = Required(bool, default=True)
    min_players = Required(int)
    max_players = Required(int)
    deck = Set(Card)
    number_of_players = Required(int, default=0)


db.bind('sqlite', 'example.sqlite', create_db=True)
db.generate_mapping(create_tables=True)
from pony.orm import (Database, PrimaryKey, Required, Set, Optional)
from enumerations import (Kind, Role, CardName)

db = Database()

class Card(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(CardName)
    description = Required(str)
    kind = Required(Kind)
    required_players = Required(int)

class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    game = Required('Game')
    position = Required(int)
    role = Required(Role)
    is_dead = Required(bool)
    hand = Set(Card)
    in_lockdown = Required(bool)
    left_barrier = Required(bool)
    right_barrier = Required(bool)

class Game(db.Entity):
    id = PrimaryKey(int, auto=True) 
    name = Required(str)
    host = Required(Player)
    players = Set(Player)
    current_turn = Required(int)
    in_game = Required(bool)
    is_done = Required(bool)
    password = Optional(str)
    going_clockwise = Required(bool)
    min_players = Required(int)
    max_players = Required(int)
    deck = Set(Card)
    discard = Set(Card)
    number_of_players = Required(int)


db.bind('sqlite', 'example.sqlite', create_db=True)
db.generate_mapping(create_tables=True)
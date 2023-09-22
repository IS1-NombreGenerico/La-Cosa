from pony.orm import (Database, PrimaryKey, Required, Set, Optional)
from enumerations import (Kind, Role, CardName)

db = Database()

""" class Card(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(CardName, default=CardName.THE_THING)
    description = Required(str, default="description")
    discarded = Required(bool, default=False)
    kind = Required(Kind, default=Kind.ACTION)
    game = Required('Game', reverse="deck")
    player = Required('Player', reverse="hand")
    required_players = Required(int, default=0) """

class User(db.Entity):
    """An User that can or nor host a game"""
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    #player = Optional("Player")
    game = Optional("Game")

class Game(db.Entity):
    """A game that can be hosted by an User"""
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    password = Optional(str)
    host = Required(User)
    in_game = Required(bool, default=False)
    min_players = Required(int, default=4)
    max_players = Required(int, default=12)

""" class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    user = Required("User")
    #game = Required('Game', reverse="players")
    position = Required(int, default=0)
    role = Required(Role, default=Role.HUMAN)
    is_dead = Required(bool, default=False)
    hand = Set(Card)
    in_lockdown = Required(bool, default=False)
    left_barrier = Required(bool, default=False)
    right_barrier = Required(bool, default=False) """

""" class Game(db.Entity):
    id = PrimaryKey(int, auto=True) 
    name = Required(str)
    host = Required(User)
    # players = Set(Player)
    current_turn = Required(int, default=0)
    in_game = Required(bool, default=False)
    is_done = Required(bool, default=False)
    password = Optional(str)
    going_clockwise = Required(bool, default=True)
    min_players = Required(int, default=4)
    max_players = Required(int, default=12)
    deck = Set(Card)
    number_of_players = Required(int, default=0) """


db.bind('sqlite', 'example.sqlite', create_db=True)
db.generate_mapping(create_tables=True)
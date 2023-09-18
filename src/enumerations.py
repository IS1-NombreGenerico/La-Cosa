from enum import Enum

class Kind(Enum):
    ACTION = 1
    DEFENSE = 2
    PANIC = 3
    THETHING = 4
    INFECTION = 5

#class CardName(Enum):
class Role(Enum):
    HUMAN = 1
    THING = 2
    INFECTED = 3

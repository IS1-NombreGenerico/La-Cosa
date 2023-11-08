from entities import Game, Player, Card
from enumerations import CardName, Kind, Role
from pony.orm import db_session, select

with db_session:
    test_card = Card(name=CardName.SWAP_PLACES)
    test_card2 = Card(name=CardName.YOU_BETTER_RUN)
    test_card3 = Card(name=CardName.FLAMETHROWER)
    player = Player(name="test_player", role=Role.HUMAN, hand=[test_card, test_card2, test_card3],position=1)
    cards = [c.name for c in player.hand]
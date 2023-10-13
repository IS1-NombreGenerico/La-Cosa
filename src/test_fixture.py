import pytest
from pony.orm import db_session
from entities import Game, Player

# Fixture para crear un juego
@pytest.fixture
@db_session
def game(request):
    game_data = request.param
    host = Player(name=game_data["host_name"])
    game = Game(
        name=game_data["game_name"],
        host=host,
        min_players=game_data["min_players"],
        max_players=game_data["max_players"],
        password=game_data["password"]
    )
    
    # Agregar jugadores a la partida
    player_names = game_data["players"].split(",")
    for player_name in player_names:
        player = Player(name=player_name.strip())
        game.players.add(player)
        game.number_of_players += 1

    return game

# Define los parámetros para crear múltiples juegos
game_params = [
    {
        "game_name": "Game A",
        "host_name": "Player A",
        "min_players": 4,
        "max_players": 6,
        "password": "password",
        "players": "Player B, Player C, Player D, Player E"
    },
    {
        "game_name": "Game B",
        "host_name": "Player B",
        "min_players": 5,
        "max_players": 11,
        "password": "secret",
        "players": "Player F, Player G, Player H, Player I, Player J, Player K, Player L, Player M"
    }
]


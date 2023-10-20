import pytest
from pony.orm import db_session, flush, select
from fastapi.testclient import TestClient
from hello import app
from config import databasename
from test_fixture import game_params, game 
from enumerations import Role
from entities import Player, Game
from all_utils.play_card import play_flamethrower, play_watch_your_back
import utils

client = TestClient(app)
databasename = "test.sqlite"

@pytest.mark.integration_test
def test_retrieve_availables_games_empty():
    """Tests that the endpoint returns an empty list when there are no games available.
    Fails if the status code is not 200 or the list is not empty."""

    response = client.get("/join")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.integration_test
def test_create_game_success():
    """Tests a create game success scenario.
    Fails if the status code is not 200 or 
    if the game id and host_id is not correct."""

    response = client.post("/", json={
        "game_name": "Game A",
        "player_name": "Player A",
        "min_players": 4,
        "max_players": 6,
        "password": "password"
    })
    assert response.status_code == 201
    assert response.json() == {"id": 1, "host_id": 1}


@pytest.mark.integration_test
def test_start_game_failure():
    """Test a start of a game failure scenario.
    Fails if the status code is not 400 or the error message is not correct.
    """

    response = client.patch("/1/1")
    assert response.status_code == 400
    assert response.json() == {"detail": "INSUFFICIENT_PLAYERS"}


@pytest.mark.integration_test
def test_create_game_failure():
    """Tests a game failure creation scenario.
    Fails if the status code is not 400 or the error message is not correct.
    """

    response = client.post("/", json={
        "game_name": "Game b",
        "player_name": "Player b",
        "min_players": 2,
        "max_players": 2,
        "password": "password"
    })
    assert response.status_code == 400
    assert response.json() == {"detail": "INVALID_SETTINGS"}


@pytest.mark.integration_test
def test_retrieve_availables_games_with_one_game():
    """Tests a retrieve of one game from the endpoint.
    Fails if the status code is not 200 or the game retrieved is not correct.
    """

    response = client.get("/join")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "Game A",
            "min_players": 4,
            "max_players": 6,
            "password": "password",
            "number_of_players": 1
        },
    ]


@pytest.mark.integration_test
def test_create_game_nopassword():
    """Test creating a game with no password scenario.
    Fails if the status code is not 201
    if the game id and host_id is not correct.
    """

    response = client.post("/", json={
        "game_name": "Game c",
        "player_name": "Player c",
        "min_players": 4,
        "max_players": 6,
        "password": ""
    })
    assert response.status_code == 201
    assert response.json() == {"id": 2, "host_id": 2}


@pytest.mark.integration_test
def test_retrieve_availables_games_with_two_games():
    """Tests a retrieve of two games from the endpoint.
    Fails if the status code is not 200 or the games retrieved are not correct.
    """

    response = client.get("/join")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "Game A",
            "min_players": 4,
            "max_players": 6,
            "password": "password",
            "number_of_players": 1
        },
        {
            "id": 2,
            "name": "Game c",
            "min_players": 4,
            "max_players": 6,
            "password": "",
            "number_of_players": 1
        }
    ]


@pytest.mark.integration_test
def test_join_game_success():
    """Tests a join game success scenario.
    Fails if status code is not 201 or if the new player id is not correct."""

    response = client.post("/join/1", json={
        "player_name": "Player B",
        "password": "password"
    })
    assert response.status_code == 201
    assert response.json() == {"id": 3}

@pytest.mark.integration_test
def test_join_game_failure():
    """Tests a join game failure scenario.
    Fails if status code is not 400 or if the error message is not correct."""

    response = client.post("/join/1", json={
        "player_name": "Player C",
        "password": "wrongpassword"
    })
    assert response.status_code == 400
    assert response.json() == {"detail": "INVALID_PASSWORD"}

@pytest.mark.integration_test
def test_join_game_no_password():
    """Tests a join game with no password scenario.
    Fails if tje status code is not 201 or if the new player id is not correct.
    """

    response = client.post("/join/2", json={
        "player_name": "Player D",
        "password": ""
    })
    assert response.status_code == 201
    assert response.json() == {"id": 4}



#Agregar jugadores para iniciar la partida
@pytest.mark.integration_test
def test_join_to_start1():
    """Populates the database to test start game endpoint."""

    response = client.post("/join/2", json={
        "player_name": "Player1",
        "password": "password"
    })
    assert response.status_code == 201
    assert response.json() == {"id": 5}

@pytest.mark.integration_test
def test_join_to_start2():
    """Populates the database to test start game endpoint."""

    response = client.post("/join/2", json={
        "player_name": "Player2",
        "password": "password"
    })
    assert response.status_code == 201
    assert response.json() == {"id": 6}

@pytest.mark.integration_test
def test_join_to_start3():
    """Populates the database to test start game endpoint."""

    response = client.post("/join/2", json={
        "player_name": "Player3",
        "password": "password"
    })
    assert response.status_code == 201
    assert response.json() == {"id": 7}

@pytest.mark.integration_test
def test_join_to_start4():
    """Populates the database to test start game endpoint."""

    response = client.post("/join/2", json={
        "player_name": "Player4",
        "password": "password"
    })
    assert response.status_code == 201
    assert response.json() == {"id": 8}



@pytest.mark.integration_test
def test_start_game_succes():
    """Tests game start success scenario.
    Fails if status code is not 200 or if the game is not started."""

    response = client.patch("/2/2")
    assert response.status_code == 200
    assert response.json() == {"message": "Game 2 Started"}


@pytest.mark.integration_test
def test_verification_start():
    response = client.get("/join")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "Game A",
            "min_players": 4,
            "max_players": 6,
            "password": "password",
            "number_of_players": 2
        }
    ]


@pytest.mark.integration_test
def test_leave_player_no_host_game():
    """Tests the exit of a player no host from a game.
    Fails if the message is not correct."""

    response = client.request("DELETE", "/1/2")
    assert response.json() == {"message": "Player 2 Deleted"}


@pytest.mark.integration_test
def test_verification_delete1():
    """Tests the available games after deleting"""

    response = client.get("/join")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "Game A",
            "min_players": 4,
            "max_players": 6,
            "password": "password",
            "number_of_players": 1
        }
    ]

@pytest.mark.integration_test
def test_leave_host_game():
    """Tests the exit of the host from the game.
    Fails if the message is not correct.
    """
    
    response = client.request("DELETE", "/1/1")
    assert response.json() == {"message": "Game 1 Deleted"}


@pytest.mark.integration_test
def test_verification_delete2():
    """Tests the available games before deleting"""

    response = client.get("/join")
    assert response.status_code == 200
    assert response.json() == []

@pytest.fixture
def game():
    with db_session:
        p1 = Player(name="Player 1",
                    position=2,
                    is_dead=False)
        p2 = Player(name="Player 2",
                position=1,
                is_dead=False)
        flush()
        g = Game(name="Game 1",
                host=p1,
                current_turn=1,
                players=[p1, p2],
                discarded = [],
                number_of_players=2)
        return g

@pytest.mark.card_test
def test_Lanzallamas(game):
    with db_session:
        game_afected = select(g for g in Game if g.id == game.id).first()
        player1 = game.players.select(lambda p: p.name == "Player 1").first()
        player2 = game.players.select(lambda p: p.name == "Player 2").first()
        prev_pos = player1.position
        play_flamethrower(game_afected, player2)
        assert player2.is_dead == True
        assert player1.position == prev_pos - 1

@pytest.mark.card_test
def test_watch_your_back(game):
    with db_session:
        game_afected = select(g for g in Game if g.id == game.id).first()
        sentido = game_afected.going_clockwise
        play_watch_your_back(game_afected)
        nuevo_sentido = game_afected.going_clockwise
        assert sentido != nuevo_sentido
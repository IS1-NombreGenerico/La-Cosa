import pytest
from fastapi.testclient import TestClient
from hello import app
from config import databasename

client = TestClient(app)
databasename = "test.sqlite"

@pytest.mark.integration_test
def test_retrieve_availables_games_empty():
    response = client.get("/join")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.integration_test
def test_create_game_success():
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
    response = client.patch("/1/1")
    assert response.status_code == 400
    assert response.json() == {"detail": "INSUFFICIENT_PLAYERS"}


@pytest.mark.integration_test
def test_create_game_failure():
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
    response = client.post("/join/1", json={
        "player_name": "Player B",
        "password": "password"
    })
    assert response.status_code == 201
    assert response.json() == {"id": 3}

@pytest.mark.integration_test
def test_join_game_failure():
    response = client.post("/join/1", json={
        "player_name": "Player C",
        "password": "wrongpassword"
    })
    assert response.status_code == 400
    assert response.json() == {"detail": "INVALID_PASSWORD"}

@pytest.mark.integration_test
def test_join_game_no_password():
    response = client.post("/join/2", json={
        "player_name": "Player D",
        "password": ""
    })
    assert response.status_code == 201
    assert response.json() == {"id": 4}



#Agregar jugadores para iniciar la partida
@pytest.mark.integration_test
def test_join_to_start1():
    response = client.post("/join/2", json={
        "player_name": "Player1",
        "password": "password"
    })
    assert response.status_code == 201
    assert response.json() == {"id": 5}

@pytest.mark.integration_test
def test_join_to_start2():
    response = client.post("/join/2", json={
        "player_name": "Player2",
        "password": "password"
    })
    assert response.status_code == 201
    assert response.json() == {"id": 6}

@pytest.mark.integration_test
def test_join_to_start3():
    response = client.post("/join/2", json={
        "player_name": "Player3",
        "password": "password"
    })
    assert response.status_code == 201
    assert response.json() == {"id": 7}

@pytest.mark.integration_test
def test_join_to_start4():
    response = client.post("/join/2", json={
        "player_name": "Player4",
        "password": "password"
    })
    assert response.status_code == 201
    assert response.json() == {"id": 8}



@pytest.mark.integration_test
def test_start_game_succes():
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
    response = client.request("DELETE", "/1/2")
    assert response.json() == {"message": "Player 2 Deleted"}


@pytest.mark.integration_test
def test_verification_delete1():
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
    response = client.request("DELETE", "/1/1")
    assert response.json() == {"message": "Game 1 Deleted"}


@pytest.mark.integration_test
def test_verification_delete2():
    response = client.get("/join")
    assert response.status_code == 200
    assert response.json() == []

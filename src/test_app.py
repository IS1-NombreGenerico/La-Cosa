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
    response = client.patch("/{id_game}", json={
        "id_player" : 1,
        "id_game" : 1
    })
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


@pytest.mark.integration_test
def test_leave_player_no_host_game():
    response = client.request("DELETE", "/{id_game}", json={
        "id_player" : 4,
        "id_game" : 2
    })
    assert response.json() == False
    

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
            "number_of_players": 2
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
def test_leave_host_game():
    response = client.request("DELETE", "/{id_game}", json={
        "id_player" : 1,
        "id_game" : 1
    })
    assert response.json() == True


@pytest.mark.integration_test
def test_verification_delete2():
    response = client.get("/join")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 2,
            "name": "Game c",
            "min_players": 4,
            "max_players": 6,
            "password": "",
            "number_of_players": 1
        }
    ]
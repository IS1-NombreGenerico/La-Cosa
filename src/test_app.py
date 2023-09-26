import pytest
from fastapi.testclient import TestClient

from hello import app

client = TestClient(app)

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
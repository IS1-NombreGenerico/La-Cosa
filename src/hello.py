from fastapi import FastAPI
from pony.orm import db_session
from entities import (User, Game, db)
from schemas import CreateGameIn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/game")
async def create_game(form: CreateGameIn) -> CreateGameIn:
    with db_session:
        host_user = User(name=form.player_name)
        game = Game(name="test", password="1234", host=host_user)
        """ player = Player(name=form.player_name, user=host_user)
        game = Game(name=form.game_name, host=host_user, min_players=form.min_players, max_players=form.max_players, password=form.password) """
    return form
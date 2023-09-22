from fastapi import FastAPI
from pony.orm import db_session
from entities import (Card, Player, Game, db)
from schemas import CreateGameIn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/game")
async def create_game(form: CreateGameIn) -> CreateGameIn:
    with db_session:
        game = Game(name=form.game_name, host=Player(name=form.player_name), min_players=form.min_players, max_players=form.max_players, password=form.password)
    return form
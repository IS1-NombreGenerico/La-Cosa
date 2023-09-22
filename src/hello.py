from fastapi import FastAPI
from typing import List
from pony.orm import db_session, select
from entities import (User, Game, db)
from schemas import CreateGameIn, GamesInfoOut

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/game")
async def create_game(form: CreateGameIn) -> CreateGameIn:
    with db_session:
        host_user = User(name=form.player_name)
        game = Game(name="test", password="1234", host=host_user, min_players=form.min_players, max_players=form.max_players)
        """ player = Player(name=form.player_name, user=host_user)
        game = Game(name=form.game_name, host=host_user, min_players=form.min_players, max_players=form.max_players, password=form.password) """
    return form

@app.get("/game")
async def show_games() -> List[GamesInfoOut]:
    with db_session:
        games = [GamesInfoOut(game_name=game.name, min_players=game.min_players, max_players=game.max_players) for game in select(g for g in Game)]
    return games
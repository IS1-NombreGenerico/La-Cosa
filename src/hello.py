from fastapi import FastAPI
from typing import List
from pony.orm import db_session, select, flush
from entities import (User, Game, db)
from schemas import CreateGameIn, GamesInfoOut, GameInDB

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/game")
async def create_game(form: CreateGameIn) -> GameInDB:
    """ Creates a new game
    Input: CreateGameIn
    --------
    Output: GameInDB
        Schema based on the game data base model
    """
    with db_session:
        host_user = User(name=form.player_name)
        game = Game(name=form.game_name, password=form.password, host=host_user, min_players=form.min_players, max_players=form.max_players)
        flush()
        game_model = GameInDB(game_id=game.id, game_name=game.name, host_id=game.host.id, min_players=game.min_players, max_players=game.max_players, password=game.password)
        """ player = Player(name=form.player_name, user=host_user)
        game = Game(name=form.game_name, host=host_user, min_players=form.min_players, max_players=form.max_players, password=form.password) """
    return game_model

@app.get("/game")
async def get_games() -> List[GamesInfoOut]:
    """ Get the list of games available
    Input: None
    -------
    Ouput: List[GamesInfoOut]
        A list of current available games
    """
    with db_session:
        games = [GamesInfoOut(game_name=game.name, min_players=game.min_players, max_players=game.max_players) for game in select(g for g in Game if g.in_game == False)]
    return games

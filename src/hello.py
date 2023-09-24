from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pony.orm import db_session, select
from entities import Player, Game
from schemas import CreateGameIn, CreateGameResponse, GameOut, PlayerIn, PlayerResponse, PlayerOut
from utils import db_game_2_game_out, db_player_2_player_out


app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/game")
async def create_game(form: CreateGameIn) -> CreateGameIn:
    return form

@app.get("/join")
async def list_availables_games() -> List[GameOut]:

    filter_by_availability = lambda g: g.number_of_players < g.max_players and not g.in_game

    with db_session:
        games = [
            db_game_2_game_out(g)
            for g in select(
                g
                for g in Game
                if filter_by_availability(g)
            )
        ]
    return games

@app.post("/join")
async def join_game(game_info: GameOut, player_info: PlayerIn) -> PlayerResponse:
    if not player_info.player_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="EMPTY_NAME",
        )
    
    if password and game_info.password != player_info.password:
        raise HTTPException(
            status_code=status.HTTP_407_INVALID_PASSWORD,
            detail="INVALID_PASSWORD",
        )

    with db_session:
        p = Player(
            name = player_info.player_name,
            game = game_info.id,
            position = game_info.number_of_players,
            role = HUMAN,
            is_dead = False,
            in_lockdown = False,
            left_barrier = False,
            right_barrier = False,
        )
        return PlayerResponse(id=p.id)

@app.delete("/{id_player}/{id_game}")
async def leave_game(id_player: int, id_game: int) -> PlayerResponse:

    with db_session:
        db_player = select(p for p in Player if p.id == id).first()
        if not db_player:
            raise HTTPException(
                status_code=status.HTTP_406_INVALID_PLAYER,
                detail="INVALID_PLAYER",
            )
        db_player.delete()
        return PlayerResponse(id=id)

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

@app.post("/join/{id_game}")
async def join_game(id_game: int, player_info: PlayerIn) -> PlayerResponse:

    if not player_info.player_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="EMPTY_NAME",
        )

    with db_session:
        
        db_game = select(g for g in Game if g.id == id).first()
        
        if not db_game:
            raise HTTPException(
                status_code=status.HTTP_408_INVALID_GAME,
                detail="INVALID_GAME",
            )
        if db_game.in_game:
            raise HTTPException(
                status_code=status.HTTP_409_GAME_IN_PROGRESS,
                detail="GAME_IN_PROGRESS",
            )
        if db_game.number_of_players >= db_game.max_players:
            raise HTTPException(
                status_code=status.HTTP_403_COMPLETE_QUOTE,
                detail="COMPLETE_QUOTE",
            )
        if db_game.password and db_game.password != player_info.password:
            raise HTTPException(
                status_code=status.HTTP_407_INVALID_PASSWORD,
                detail="INVALID_PASSWORD",
            )

        p = Player(
            name = player_info.player_name,
            game = db_game,
            position = db_game.number_of_players,
            role = HUMAN,
            is_dead = False,
            in_lockdown = False,
            left_barrier = False,
            right_barrier = False,
        )

        db_game.number_of_players += 1
        db_game.players.add(p)

    return PlayerResponse(id=p.id)

@app.delete("/{id_game}/{id_player}")
async def leave_game(id_game: int, id_player: int) -> PlayerResponse:

    with db_session:
    
        db_player = select(p for p in Player if p.id == id).first()
        db_game = select(g for g in Game if g.id == id).first()

        if not db_player:
            raise HTTPException(
                status_code=status.HTTP_406_INVALID_PLAYER,
                detail="INVALID_PLAYER",
            )
        if not db_game:
            raise HTTPException(
                status_code=status.HTTP_408_INVALID_GAME,
                detail="INVALID_GAME",
            )
        if db_game.host == db_player:
            raise HTTPException(
                status_code=status.HTTP_401_IS_HOST,
                detail="IS_HOST",
            )

        db_player.delete()
        db_game.number_of_players -= 1

    return PlayerResponse(id=id)

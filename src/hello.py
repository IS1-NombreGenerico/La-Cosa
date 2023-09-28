from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pony.orm import db_session, select, flush
from entities import Player, Game
from enumerations import Role
from schemas import CreateGameIn, CreateGameResponse, GameOut, PlayerIn, PlayerResponse, PlayerOut, GameInDB, PlayerInDB
from utils import db_game_2_game_out, db_game_2_game_schema, db_player_2_player_schema

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/", status_code=status.HTTP_201_CREATED)
async def create_game(form: CreateGameIn) -> CreateGameResponse:
    """ Creates a new game
    Input: CreateGameIn
    --------
    Output: CreateGameResponse
        Information about the game and host
    """
    if form.min_players > form.max_players:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_SETTINGS"
        )
    with db_session:
        try:
            host = Player(name=form.player_name)
            flush()
            game = Game(name=form.game_name, host=host, players=[host], 
            min_players=form.min_players, max_players=form.max_players, password=form.password)
            host.game = game
            host.host = game
            flush()
        except: raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_SETTINGS"
        )
        response = CreateGameResponse(id=game.id, host_id=game.host.id)
    return response

@app.get("/join")
async def retrieve_availables_games() -> List[GameOut]:
    """ Get the list of games available
    Input: None
    -------
    Ouput: List[GameOut]
        A list of current available games
    """
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

@app.post("/join/{game_id}", status_code=status.HTTP_201_CREATED)
async def join_game(game_id: int, player_info: PlayerIn) -> PlayerResponse:
    """ Join a game
    Input: PlayerIn
    -------
    Output: PlayerResponse
        
    """
    if not player_info.player_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="EMPTY_NAME"
        )

    with db_session:
        
        db_game = select(g for g in Game if g.id == game_id).first()
        
        if not db_game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="INVALID_GAME"
            )
        if db_game.in_game:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GAME_IN_PROGRESS"
            )
        if db_game.number_of_players >= db_game.max_players:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="COMPLETE_QUOTE"
            )
        if db_game.password and db_game.password != player_info.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_PASSWORD"
            )

        p = Player(name = player_info.player_name, game = db_game, position = db_game.number_of_players)
        
        db_game.number_of_players += 1
        flush()

        response = PlayerResponse(id=p.id)

    return response

@app.delete("/{id_game}")
async def leave_game(id_game: int, id_player: int): #falta modificar

    with db_session:
    
        db_player = select(p for p in Player if p.id == id).first()
        db_game = select(g for g in Game if g.id == id).first()

        if not db_player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="INVALID_PLAYER"
            )
        if not db_game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="INVALID_GAME"
            )
        if db_game.host == db_player:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="IS_HOST"
            )

        db_player.delete()
        db_game.number_of_players -= 1

    return PlayerResponse(id=id)

@app.get("/player/{player_id}")
async def get_player_info(player_id: int) -> PlayerInDB:
    """Returns Player information
    Input: player_id
    --------
    Ouput: PlayerInDB
        Player Information
    """
    with db_session:
        db_player = select(p for p in Player if p.id == player_id).first()
        if not db_player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="INVALID_PLAYER"
            )
        player = db_player_2_player_schema(db_player)
    return player

@app.get("/game/{game_id}")
async def get_game_info(game_id: int) -> GameInDB:
    """Returns Game information
    Input: game_id
    ---------
    Output: GameInDB
        Information about the game
    """
    with db_session:
        db_game = select(g for g in Game if g.id == game_id).first()
        if not db_game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="INVALID_GAME"
            )
        players = [db_player_2_player_schema(p) for p in db_game.players]
        game = db_game_2_game_schema(db_game, players)
        return game

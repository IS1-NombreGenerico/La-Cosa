from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pony.orm import db_session, select, flush
from entities import Player, Game, Card
from enumerations import Role, Kind
from schemas import CreateGameIn, CreateGameResponse, GameOut, PlayerIn, PlayerResponse, PlayerOut, GameInDB, PlayerInDB, GameStart
from utils import db_game_2_game_out, db_game_2_game_schema, db_player_2_player_schema, validate_game, validate_player, shuffle_and_assign_positions, create_deck
import random

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
        
        db_game = validate_game(game_id)

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
        
        db_game.players.add(p)
        db_game.number_of_players += 1
        flush()

        response = PlayerResponse(id=p.id)

    return response

@app.delete("/{id_game}")
async def leave_game(game_info: GameStart) -> bool:
    """Leave a game
    Input: GameStart - game_id
    ---------
    Output: Delete game(True)/Delete player(False) 
    """
    with db_session:
        game = validate_game(game_info.id_game)

        if game.host.id == game_info.id_player:
            players_of_game = Player.select(lambda p: p.game.id == game_info.id_game)
            for player in players_of_game:
                player.delete()
            game_deleted = True
        else:
            player = validate_player(game_info.id_player)
            player.delete()
            game.number_of_players -= 1
            game_deleted = False

        return game_deleted

@app.get("/player/{player_id}")
async def get_player_info(player_id: int) -> PlayerInDB:
    """Returns Player information
    Input: player_id
    --------
    Ouput: PlayerInDB
        Player Information
    """
    with db_session:
        db_player = validate_player(player_id)
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
        db_game = validate_game(game_id)
        players = [db_player_2_player_schema(p) for p in db_game.players]
        game = db_game_2_game_schema(db_game, players)
        return game


@app.patch("/{id_game}", status_code=status.HTTP_200_OK)
async def start_game(game_info: GameStart) -> bool:
    """Starts the game
    Input: GameStart - game_id
    ---------
    Ouput: Success/Failure
    """
    with db_session:
        player = validate_player(game_info.id_player)
        game = validate_game(game_info.id_game)
        
        if len(game.players) < game.min_players:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INSUFFICIENT_PLAYERS"
            )

        if player != game.host:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_ACTION"
            )
        
        game.in_game = True

        outplayers = shuffle_and_assign_positions(game.players)
        create_deck(game.id)
        
        return True
    
@app.get("/{id_game}")
async def deal_cards(id_game: int):
    with db_session:
        db_game = validate_game(id_game)

        cards_list = list(db_game.deck)
        random.shuffle(cards_list)

        card_theThing = Card.get(name="THE_THING")
        theThing = random.randint(1, db_game.number_of_players)

        for player in db_game.players:
            num_cards = 3 if player.position == theThing else 4
            eligible_kinds = {Kind.ACTION, Kind.DEFENSE}

            for _ in range(num_cards):
                valid_cards = [Card for Card in cards_list if Card.kind in eligible_kinds]
                if valid_cards:
                    selected_card = valid_cards.pop()
                    player.hand.add(selected_card)

            if player.position == theThing:
                player.hand.add(card_theThing)
                player.role = Role.THING
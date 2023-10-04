from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pony.orm import db_session, select, flush
from entities import Player, Game
from enumerations import Role
from schemas import CreateGameIn, CreateGameResponse, GameOut, PlayerIn, PlayerResponse, PlayerOut, GameInDB, PlayerInDB, CardIn, GameProgress, CardOut
import utils

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
        Information about the game (name, host, min_players, max_players, password)
    --------
    Output: CreateGameResponse
        Information about the game and host (id, host_id)
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
            utils.db_game_2_game_out(g)
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
        Information about the player and game (player name, game password)
    -------
    Output: PlayerResponse   
        Information about the player (id)
    """
    if not player_info.player_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="EMPTY_NAME"
        )

    with db_session:
        
        db_game = utils.validate_game(game_id)

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

@app.delete("/{id_game}/{id_player}")
async def leave_game(id_game: int, id_player: int) -> dict:
    """Leave a game
    Input: None
    ---------
    Output: Deleted game (Bool)
    """
    with db_session:
        game = utils.validate_game(id_game)

        if game.host.id == id_player:
            players_of_game = Player.select(lambda p: p.game.id == id_game)
            for player in players_of_game:
                player.delete()
            return {"message": f"Game {id_game} Deleted"}
        else:
            player = utils.validate_player(id_player)
            player.delete()
            game.number_of_players -= 1
            return {"message": f"Player {id_player} Deleted"}


@app.get("/player/{player_id}")
async def get_player_info(player_id: int) -> PlayerInDB:
    """Returns Player information
    Input: player_id
    --------
    Ouput: PlayerInDB
        Player Information
    """
    with db_session:
        db_player = utils.validate_player(player_id)
        player = utils.db_player_2_player_schema(db_player)
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
        db_game = utils.validate_game(game_id)
        players = [utils.db_player_2_player_schema(p) for p in db_game.players]
        game = utils.db_game_2_game_schema(db_game, players)
        return game


@app.patch("/{id_game}/{id_player}", status_code=status.HTTP_200_OK)
async def start_game(id_game: int, id_player: int) -> dict:
    """Starts the game
    Input: none
    ---------
    Ouput: Success/Failure
    """
    with db_session:
        player = utils.validate_player(id_player)
        game = utils.validate_game(id_game)
        
        if game.number_of_players < game.min_players:
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

        outplayers = utils.shuffle_and_assign_positions(game.players)
        utils.create_deck(game.id)
        
        return {"message": f"Game {id_game} Started"}
    
@app.patch('/game/{id_game}/turn', status_code=status.HTTP_200_OK)
async def draw_card(id_game: int, id_player: int) -> bool:
    """Draws a card to the given player"""
    with db_session:
        game = utils.validate_game(id_game)
        if(game.in_game):
            return utils.draw_card(game, id_player)
    return True

@app.patch("/game/{id_game}/card/{id_card}", status_code=status.HTTP_200_OK)
async def play_card(id_game: int, id_card: int, id_player: int) -> bool:
    """Plays a card
    Input: id_game, id_card, id_player
    ---------
    Output: Success/Failure
    """
    with db_session:
        game = utils.validate_game(id_game)
        if(utils.validate_card(id_card, id_player) 
            and utils.with_single_target(id_card)):
            return utils.play_card_with_target(game, id_card, id_player)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_CARD"
            )

@app.patch("{id_game}/{id_player}/play", status_code=status.HTTP_200_OK)
async def play_card(id_game: int, id_player: int, card_info: CardIn, id_player_afected: int) -> GameProgress:
    """Plays a card
    Input: 
        id_player_afected
        CardIn (id)
            Information about the card
    ---------
    Output: GameProgress
        Information about the game progress
    """

    with db_session:
        game = utils.validate_game(id_game)
        player = utils.validate_player(id_player)
        player_afected = utils.validate_player(id_player_afected)
        card = utils.validate_card(card_info.card_id, id_player)

        if player.position != game.current_turn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="NOT_ON_TURN"
            )

        if card.kind != Kind.ACTION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_PLAY"
            )
        
        if implemented_card(card):
            match card.name:
                case card.FLAMETHROWER:
                    utils.play_flamethrower(card, player_afected)
                case _:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="INVALID_CARD"
                    )
        
        player.hand.remove(card)
        game.discarded.add(card)

        game.current_turn = (game.current_turn + 1) % game.number_of_players

        return db_game_2_game_progress(game)

@app.get("/{id_game}/{id_player}/play", status_code=status.HTTP_200_OK)
async def retrieve_information(id_game: int, id_player:int, card_info: CardIn) -> CardOut:
    """Returns information about a card
    Input: CardIn (id)
    ---------
    Output: CardOut
        Information about the card
    """
    with db_session:
        game = utils.validate_game(id_game)
        player = utils.validate_player(id_player)
        card = utils.validate_card(card_info.card_id, id_player)

        return utils.db_card_2_card_out(card, player)
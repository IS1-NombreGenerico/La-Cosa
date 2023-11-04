from typing import List, Optional
import datetime

from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pony.orm import db_session, select, flush
from entities import Player, Game
from enumerations import Role, Kind, CardName
from connection_manager import ConnectionManager
from schemas import CreateGameIn, CreateGameResponse, GameOut, PlayerIn, PlayerId, PlayerOut, GameInDB, PlayerInDB, GameProgress, CardOut
from messages import *

import utils
import play_card as card_actions
import websocket_messages
import asyncio

app = FastAPI()

connection_manager = ConnectionManager()

event_join = asyncio.Queue()

def get_time():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

@app.get("/")
async def get():
    return HTMLResponse(html)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/{user_id}", status_code=status.HTTP_201_CREATED)
async def create_game(user_id: int, form: CreateGameIn) -> CreateGameResponse:
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
        await connection_manager.broadcast(0, f"{PULL_GAMES} {get_time()}")
        connection_manager.socket_to_player[user_id] = game.host.id
        connection_manager.player_to_socket[game.host.id] = user_id
        connection_manager.game_to_users[game.id].append(user_id)
        connection_manager.game_to_users[0].remove(user_id)
        connection_manager.user_state[user_id] = START
    return response

#HAY QUE VER SI ESTE ENDPOINT SIGUE SIEDO REALMENTE NECESARIO
@app.get("/join")
async def retrieve_availables_games() -> List[GameOut]:
    """ Get the list of games available
    Input: None
    -------
    Ouput: List[GameOut]
        A list of current available games
    """
    with db_session:
        games = utils.obtain_games_available()
    
    return games

@app.post("/join/{game_id}/{user_id}", status_code=status.HTTP_201_CREATED)
async def join_game(game_id: int, user_id: int, player_info: PlayerIn) -> PlayerId:
    """ Join a game
    Input: PlayerIn
        Information about the player and game (player name, game password)
    -------
    Output: PlayerId   
        Information about the player (id)
    """
    if not player_info.player_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="EMPTY_NAME"
        )

    with db_session:
        
        # Get the relevant game
        db_game = utils.validate_game(game_id)

        # Validate game data
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

        # Update database
        p = Player(name=player_info.player_name, game=db_game, position=db_game.number_of_players)
        db_game.players.add(p)
        db_game.number_of_players += 1
        flush()
        
        # Update connection manager
        connection_manager.socket_to_player[user_id] = p.id
        connection_manager.player_to_socket[p.id] = user_id
        connection_manager.game_to_users[game_id].append(user_id)
        connection_manager.game_to_users[0].remove(user_id)
        connection_manager.user_state[user_id] = START
        await connection_manager.broadcast(0, f"{PULL_GAMES} {get_time()}")
        await connection_manager.broadcast(game_id, f"{UPDATE_GAME} {get_time()}")

        # Set up the expected response
        response = PlayerId(id=p.id)

        '''
        await connection_manager.connect(game_id, websocket)
        #acá se agregaría la lógica de agregar un identificador juego-jugador
        p = Player(name = player_info.player_name, game = db_game, position = db_game.number_of_players)
        
        db_game.players.add(p)
        db_game.number_of_players += 1
        flush()
        await connection_manager.send_lobby_info(game_id, utils.game_data_sample(db_game))
        
        response = PlayerId(id=p.id)
        ''' # TODO: Mejor hacer esto en START

    return response

@app.delete("/{id_game}/{id_player}/{id_user}")
async def leave_game(id_game: int, id_player: int, id_user: int) -> dict:
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
            # update connection manager
            for user in connection_manager.game_to_users[id_game]:
                await connection_manager.move_user(user, id_game, 0, JOIN)
            
            # return response

            return {"message": f"Game {id_game} Deleted"}
        else:
            player = utils.validate_player(id_player)
            player.delete()
            game.number_of_players -= 1
            await connection_manager.move_user(id_user, id_game, 0, JOIN)
            #si se agrega un identificador juego-jugador acá abría que eliminarlo
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
        player = utils.db_player_2_player_schemas(db_player)
    return player

@app.get("/game/{game_id}")
async def get_game_info(game_id: int) -> GameInDB:
    """Returns Game information
    Input: game_id
    ---------
    Output: GameInDB
        Information about the game
    """
    #preguntar que versión debería persistir
    with db_session:
        game = utils.validate_game(game_id)
        game_data = utils.game_data_sample(game)
        return game_data


@app.patch("/{id_game}/{id_player}/{id_user}", status_code=status.HTTP_200_OK)
async def start_game(id_game: int, id_player: int, id_user: int) -> dict:
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

        utils.shuffle_and_assign_positions(game.players)
        utils.create_deck(game.id)
        utils.deal_cards(game.id)
        flush()
        await connection_manager.broadcast(0, f"{PULL_GAMES} {get_time()}")
        for user in connection_manager.game_to_users[id_game]:
            await connection_manager.move_user(id_user, id_game, id_game, PLAY)
        await connection_manager.broadcast(0, f"{PULL_GAMES} {get_time()}")
        return utils.game_data_sample(game)
    
@app.patch('/game/{id_game}/turn', status_code=status.HTTP_200_OK)
async def draw_card(id_game: int, id_player: int) -> bool:
    """Draws a card to the given player"""
    with db_session:
        game = utils.validate_game(id_game)
        player = utils.validate_player(id_player)
        if(game.in_game and player.position == game.current_turn):
            utils.draw_card(game, player)
            flush()
            await connection_manager.broadcast(game.id, websocket_messages.GameEvents(player_name=player.name).play_card())
        elif(game.in_game and player.position != game.current_turn and len(player.hand) == 3):
            utils.draw_card(game, player)
            flush()
            await connection_manager.broadcast(game.id, websocket_messages.GameEvents(player_name=player.name).wait())
        else: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_ACTION")
        await connection_manager.send_lobby_info(id_game, utils.game_data_sample(game))
        await connection_manager.broadcast(game.id, websocket_messages.InGameMessages(player_name=player.name).new_turn())
    return True

@app.patch("/{id_game}/{id_player}/{id_card}/{id_player_afected}", status_code=status.HTTP_200_OK)
async def play_card(id_game: int, id_player: int, id_card: int, id_player_afected: int) -> dict:
    """Plays a card
    Input: 
        id_player_afected
    ---------
    Output: GameProgress
        Information about the game progress
    """
    with db_session:
        game = utils.validate_game(id_game)
        player = utils.validate_player(id_player)
        card = utils.validate_card(id_card, id_player)

        if card.name == CardName.WATCH_YOUR_BACK:
            if not (id_player_afected is None):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="INVALID_PLAY"
                )
        else:
            player_afected = utils.validate_player(id_player_afected)

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
        
        match card.name: 
            case CardName.FLAMETHROWER:
                card_actions.play_flamethrower(game, player_afected)
            case CardName.WATCH_YOUR_BACK:
                mensaje = card_actions.play_watch_your_back(game)
            case CardName.SWAP_PLACES:
                mensaje = card_actions.play_swap_places(game, player, player_afected)
            case CardName.YOU_BETTER_RUN:
                mensaje = card_actions.play_you_better_run(player ,player_afected)
            case CardName.SEDUCTION:
                mensaje = card_actions.play_seduction(player, player_afected)
            case CardName.ANALYSIS:
                mensaje = card_actions.show_cards_to_player(player_afected)
            case CardName.WHISKY:
                mensaje = card_actions.show_cards_to_player(player)
            case _:
                pass
        
        utils.discard_card(game, player, card)
        #se hace acá para primer probar la funcionalidad sin intercamio de cartas
        turn = utils.change_turn(game)
        await connection_manager.broadcast(game.id, websocket_messages.GameEvents(player_name=player.name).draw_card())
        utils.db_game_2_game_progress(game)
        return {"game_progress": utils.db_game_2_game_progress(game), 
                "message": mensaje}

@app.get("/{id_game}/{id_player}/{id_card}", status_code=status.HTTP_200_OK)
async def retrieve_information(id_game: int, id_player:int, id_card: int) -> CardOut:
    """Returns information about a card
    Input: 
    ---------
    Output: CardOut
        Information about the card
    """
    with db_session:
        game = utils.validate_game(id_game)
        player = utils.validate_player(id_player)
        card = utils.validate_card(id_card, id_player)

        return utils.db_card_2_card_out(card, player)

@app.delete("/{id_game}/{id_player}/{id_card}", status_code=status.HTTP_200_OK)
async def discard_card(id_game: int, id_player:int, id_card: int) -> bool:
    """Discards a card from player hand"""
    with db_session:
        game = utils.validate_game(id_game)
        player = utils.validate_player(id_player)
        card = utils.validate_card(id_card, id_player)
        utils.discard_card(game, player, card)
        flush()
        #await connection_manager.send_lobby_info(id_game, utils.game_data_sample(game))
        #await connection_manager.broadcast(game.id, websocket_messages.InGameMessages(player_name=player.name, card=card.name).discard())
    
    return True

#revaluar todo este endpoint en general
@app.post("/{id_game}/{id_player}/{id_card}", status_code=status.HTTP_200_OK)
async def exchange_card(id_game: int, id_player:int, id_card1: int, id_card2: int) -> GameProgress:
    """Exchanges a card with another player"""
    with db_session:
        game = utils.validate_game(id_game)
        player1 = utils.validate_player(id_player)
        if game.going_clockwise:
            player2_id = select(p for p in Player if p.game == game and p.position == ((player1.position + 1) % game.number_of_players)).first().id
        else:
            player2_id = select(p for p in Player if p.game == game and p.position == ((player1.position - 1) % game.number_of_players)).first().id
        player2 = utils.validate_player(player2_id)
        card1 = utils.validate_card(id_card1, id_player)
        card2 = utils.validate_card(id_card2, player2.id)

        if player1.is_dead or player2.is_dead or player2.in_lockdown:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_PLAY"
            )
        utils.exchange_card(player1, player2, card1, card2)
        return utils.db_game_2_game_progress(game)

@app.delete("/{id_game}", status_code=status.HTTP_200_OK)
async def finish_game(id_game: int) -> dict:
    """Finishes the game
    Input: none
    ---------
    Ouput: List of winners
    """
    with db_session:
        game = utils.validate_game(id_game)
        if(game.in_game):
            game.in_game = False
            response = utils.get_winners(game)
            players_of_game = Player.select(lambda p: p.game.id == id_game)
            for player in players_of_game:
                player.delete()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_ACTION"
            )
        flush()
        #await connection_manager.send_lobby_info(id_game, utils.game_data_sample(game))
        #await connection_manager.remove_all_connection_of_game(id_game)
    return response

@app.websocket("/ws/join")
async def websocket_join(websocket: WebSocket):
    user_id = await connection_manager.connect(0, websocket)
    await websocket.send_text("USER ID: " + str(user_id))
    connection_manager.user_state[user_id] = JOIN
    connection_manager.game_to_users[0].append(user_id) #TODO magical number 0
    try:
        while True:
            await asyncio.sleep(0.1)    
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)

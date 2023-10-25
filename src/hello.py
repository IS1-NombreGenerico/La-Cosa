from typing import List, Optional
from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pony.orm import db_session, select, flush
from entities import Player, Game
from enumerations import Role, Kind, CardName
from connection_manager import ConnectionManager
from schemas import CreateGameIn, CreateGameResponse, GameOut, PlayerIn, PlayerId, PlayerOut, GameInDB, PlayerInDB, GameProgress, CardOut
import all_utils.play_card as play_card
import utils
import websocket_messages
import asyncio

app = FastAPI()

connection_manager = ConnectionManager()

join_event = asyncio.Event()

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

    with db_session:
        games = utils.obtain_games_available()
    
    return games

@app.post("/join/{game_id}", status_code=status.HTTP_201_CREATED)
async def join_game(game_id: int, player_info: PlayerIn) -> PlayerId:
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

        response = PlayerId(id=p.id)

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
            await connection_manager.broadcast(game.id, websocket_messages.LobbyMessages(player_name=player.name, game_name=game.name).left_message())
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
    with db_session:
        db_game = utils.validate_game(game_id)
        players = [utils.db_player_2_player_schemas(p) for p in db_game.players]
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

        utils.shuffle_and_assign_positions(game.players)
        utils.create_deck(game.id)
        utils.deal_cards(game.id)
        flush()
        await connection_manager.send_lobby_info(id_game, utils.game_data_sample(game))
        await connection_manager.broadcast(game.id, websocket_messages.InGameMessages(game_name=game.name).start_message())
        return {"message": f"Game {id_game} Started"}
    
@app.patch('/game/{id_game}/turn', status_code=status.HTTP_200_OK)
async def draw_card(id_game: int, id_player: int) -> bool:
    """Draws a card to the given player"""
    with db_session:
        game = utils.validate_game(id_game)
        player = utils.validate_player(id_player)
        if game.in_game and player.position == game.current_turn and player.is_dead == False:
            utils.draw_card(game, player)
            flush()
        else: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_ACTION")
        await connection_manager.send_lobby_info(id_game, utils.game_data_sample(game))
        await connection_manager.broadcast(game.id, websocket_messages.InGameMessages(player_name=player.name).new_turn())
    return True

@app.patch("/{id_game}/{id_player}/{id_card}", status_code=status.HTTP_200_OK)
async def play_card(id_game: int, id_player: int, id_card: int, id_player_afected: int) -> GameProgress:
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
                play_card.play_flamethrower(card, player_afected)
                await connection_manager.broadcast(game.id, 
                                            websocket_messages.InGameMessages(player_name=player.name, player_target=player_afected.name, card=card.name)
                                            .targeted_card_played())
            case CardName.WATCH_YOUR_BACK:
                play_card.play_watch_your_back(game, card)
                await connection_manager.broadcast(game.id,
                                            websocket_messages.InGameMessages(player_name=player.name, card=card.name).card_played())
            case CardName.SWAP_PLACES:
                play_card.play_swap_places(card, player, player_afected)
                await connection_manager.broadcast(game.id, 
                                            websocket_messages.InGameMessages(player_name=player.name, player_target=player_afected.name, card=card.name)
                                            .targeted_card_played())
            case CardName.YOU_BETTER_RUN:
                play_card.play_you_better_run(card, player_afected)
                await connection_manager.broadcast(game.id, 
                                            websocket_messages.InGameMessages(player_name=player.name, player_target=player_afected.name, card=card.name)
                                            .targeted_card_played())
            case CardName.SEDUCTION:
                play_card.play_seduction(card, player_afected)
                await connection_manager.broadcast(game.id, 
                                            websocket_messages.InGameMessages(player_name=player.name, player_target=player_afected.name, card=card.name)
                                            .targeted_card_played())
            case CardName.ANALYSIS:
                play_card.play_analysis(card, player_afected)
                await connection_manager.broadcast(game.id, 
                                            websocket_messages.InGameMessages(player_name=player.name, player_target=player_afected.name, card=card.name)
                                            .targeted_card_played())
            case CardName.AXE:
                play_card.play_axe(card, player_afected)
                await connection_manager.broadcast(game.id, 
                                            websocket_messages.InGameMessages(player_name=player.name, player_target=player_afected.name, card=card.name)
                                            .targeted_card_played())
            case CardName.SUSPICION:
                play_card.play_suspicion(card, player_afected)
                await connection_manager.broadcast(game.id, 
                                            websocket_messages.InGameMessages(player_name=player.name, player_target=player_afected.name, card=card.name)
                                            .targeted_card_played())
            case CardName.WHISKY:
                play_card.play_whisky(card)
                await connection_manager.broadcast(game.id,
                                            websocket_messages.InGameMessages(player_name=player.name, card=card.name).card_played())
            case _:
                await connection_manager.broadcast(game.id,
                                            websocket_messages.InGameMessages(player_name=player.name, card=card.name).card_played() + " (NOT IMPLEMENTED)")
        utils.discard_card(game, player, card)
        flush()
        await connection_manager.send_lobby_info(id_game, utils.game_data_sample(game))
        return utils.db_game_2_game_progress(game)

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
    """Discards a card from the player's hand"""
    with db_session:
        game = utils.validate_game(id_game)
        player = utils.validate_player(id_player)
        card = utils.validate_card(id_card, id_player)
        utils.discard_card(game, player, card)
        flush()
        await connection_manager.send_lobby_info(id_game, utils.game_data_sample(game))
        await connection_manager.broadcast(game.id, websocket_messages.InGameMessages(player_name=player.name, card=card.name).discard())
    return True



@app.post("/{id_game}/{id_player}/{id_card}", status_code=status.HTTP_200_OK)
async def exchange_card(id_game: int, id_player:int, id_card: int, id_card2: int) -> GameProgress:
    """Exchange a card with a player based in the direction of turn"""
    #Se deberia checker desde el front que no sean jugadores muertos
    with db_session:
        game = utils.validate_game(id_game)
        player1 = utils.validate_player(id_player)
        player2 = utils.validate_player(game.players[player1.position + 1 % game.number_of_players].id if game.going_clockwise 
                                    else game.players[player1.position - 1 % game.number_of_players].id)
        card1 = utils.validate_card(id_card, id_player)
        card2 = utils.validate_card(id_card2, player2.id)
        utils.exchange_card(game, player1, player2, card1, card2)
        flush()
        await connection_manager.send_lobby_info(id_game, utils.game_data_sample(game))
        await connection_manager.broadcast(game.id,websocket_messages.InGameMessages(player_name=player1.name, 
                                                                                    player_target=player2.name, card=card1.name).exchange())
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
            return response
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_ACTION"
            )
        

#Prueba de websocket
""" @app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await connection_manager.connect(0, websocket)
    checks = set()
    for connection in connection_manager.active_connections[0]:
        print(f"Connection in manager.connections: {connection}")
        print(f"Socket passed as argument to endpoint: {websocket}")
        checks.add(connection == websocket)
    assert True in checks
    try:
        while True:
            data = await websocket.receive_text()
            await connection_manager.send_personal_message(0, f"You wrote: {data}", websocket)
            await connection_manager.broadcast(0, f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        connection_manager.disconnect(0, websocket)
        await connection_manager.broadcast(0, f"Client #{client_id} left the chat") """

@app.get("/")
async def get():
    return HTMLResponse(html)

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

@app.websocket("/ws/join")
async def websocket_join(websocket: WebSocket) -> list[GameOut]:
    await connection_manager.connect(0, websocket)
    try:
        with db_session:
            games = utils.obtain_games_available()
            await join_event.wait()
            connection_manager.disconnect(0, websocket)
    except WebSocketDisconnect:
        connection_manager.disconnect(0, websocket)
    return games

@app.websocket("/ws/")
async def websocket_create_game(websocket: WebSocket, form: CreateGameIn) -> CreateGameResponse:
    
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
            games = utils.obtain_games_available()    
            try:
                #Disconnect websocket from main menu group
                join_event.set()
                await connection_manager.connect(game.id, websocket)
                #Broadcast refresh games to main menu group
                await connection_manager.send_games(games)
            except: raise HTTPException("Connection not found")
            response = CreateGameResponse(id=game.id, host_id=game.host.id)
        except: raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_SETTINGS"
        )

    return response

@app.websocket("/ws/lobby/{game_id}")
async def websocket_join_game(websocket: WebSocket, game_id: int, player_info: PlayerIn) -> PlayerId:
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

        join_event.set()
        await connection_manager.connect(game_id, websocket)
        p = Player(name = player_info.player_name, game = db_game, position = db_game.number_of_players)
        
        db_game.players.add(p)
        db_game.number_of_players += 1
        flush()
        await connection_manager.send_lobby_info(game_id, utils.game_data_sample(db_game))
        response = PlayerId(id=p.id)

    return response
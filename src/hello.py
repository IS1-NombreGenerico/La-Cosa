from typing import List, Optional
from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pony.orm import db_session, select, flush
from entities import Player, Game
from enumerations import Role, Kind, CardName
from connection_manager import ConnectionManager
from schemas import CreateGameIn, CreateGameResponse, GameOut, PlayerIn, PlayerId, PlayerOut, GameInDB, PlayerInDB, GameProgress, CardOut
import utils
import all_utils.play_card as card_actions
import websocket_messages

app = FastAPI()

connection_manager = ConnectionManager()

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
        game = utils.validate_game(game_id)
        game_data = utils.game_data_sample(game)
        return game_data


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
        
        return {"message": f"Game {id_game} Started"}
    
@app.patch('/game/{id_game}/turn', status_code=status.HTTP_200_OK)
async def draw_card(id_game: int, id_player: int) -> bool:
    """Draws a card to the given player"""
    with db_session:
        game = utils.validate_game(id_game)
        player = utils.validate_player(id_player)
        if(game.in_game and player.position == game.current_turn):
            return utils.draw_card(game, player)
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
                mensaje = card_actions.play_watch_your_back(game, card)
            case CardName.SWAP_PLACES:
                mensaje = card_actions.play_swap_places(card, player, player_afected)
            case CardName.YOU_BETTER_RUN:
                mensaje = card_actions.play_you_better_run(card, player_afected)
            case CardName.SEDUCTION:
                mensaje = card_actions.play_seduction(player, frt_card, player_afected, sec_card)
            case CardName.ANALYSIS:
                mensaje = card_actions.show_cards_to_player(player_afected)
            case CardName.WHISKY:
                mensaje = card_actions.show_cards_to_player(player)
            case _:
                pass
        
        utils.discard_card(game, player, card)
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
    return True

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
            return response
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_ACTION"
            )
        
#Prueba de websocket
"""@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await connection_manager.connect(0, websocket)
    with db_session:
        try:
            while True:
                games = utils.obtain_games_available()
                data = await websocket.receive_text()
                await connection_manager.send_personal_message(0, f"You wrote: {data}", websocket)
                await connection_manager.broadcast(0, f"Client #{client_id} says: {data}")
                await connection_manager.send_games(games)
        except WebSocketDisconnect:
            connection_manager.disconnect(0, websocket)
            await connection_manager.broadcast(0, f"Client #{client_id} left the chat")"""

@app.get("/test")
async def get():
    return HTMLResponse(html)

html = """
<!DOCTYPE html>
<html>
<head>
    <title>Chat</title>
</head>
<body>
    <h1>WebSocket with FastAPI</h1>
    <form action="" onsubmit="sendMessage(event)">
        <input type="text" id="messageText" autocomplete="off" />
        <button>Send</button>
    </form>
    <ul id='messages'>
    </ul>
    <script>
        var ws = new WebSocket(`ws://localhost:8000/ws/join`);
        request = new XMLHttpRequest(url, form, ws);
        console.log("Connected")
        ws.onmessage = function (event) {
            var messages = document.getElementById('messages')
            var message = document.createElement('li')
            var content = document.createTextNode(event.data)
            message.appendChild(content)
            messages.appendChild(message)
        };
        console.log("Send Mesage")
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
#Prueba de websocket
@app.websocket("/ws/join")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(0, websocket)
    with db_session:
        try:
            games = utils.obtain_games_available()
            await connection_manager.send_games(games)
            while True:
                await connection_manager.handle_connection(0, websocket)
        except WebSocketDisconnect:
            connection_manager.disconnect(0, websocket)

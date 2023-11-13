from typing import List, Optional
import datetime

from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pony.orm import db_session, select, flush
from entities import Player, Game
from enumerations import Role, Kind, CardName, Status
from connection_manager import ConnectionManager
from schemas import CreateGameIn, CreateGameResponse, GameOut, PlayerIn, PlayerId, PlayerOut, GameInDB, PlayerInDB, GameProgress, CardOut
from messages import *
from chat import Messages

import utils
import play_card as card_actions
import asyncio

app = FastAPI()

connection_manager = ConnectionManager()
chat = Messages()
event_join = asyncio.Queue()

GAMES_LIST_ID = 0
SINGLE_ARGUMENT_CARDS = set([
    "WHISKY",
    "DETERMINATION"
])

def get_time():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

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

        # update connection manager
        await connection_manager.move_user(user_id, GAMES_LIST_ID, game.id, START)

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
        await connection_manager.move_user(user_id, GAMES_LIST_ID, game_id, START)

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
                await connection_manager.move_user(user, id_game, GAMES_LIST_ID, JOIN)

            # return response

            return {"message": f"Game {id_game} Deleted"}
        else:
            player = utils.validate_player(id_player)
            player.delete()
            game.number_of_players -= 1
            await connection_manager.move_user(id_user, id_game, GAMES_LIST_ID, JOIN)
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
        utils.change_turn(game.id)
        flush()
        player_turn = select(p for p in game.players if p.position == game.current_turn).first()
        print(f"Turno de {player_turn.name}")
        for user in connection_manager.game_to_users[id_game]:
            await connection_manager.move_user(id_user, id_game, id_game, PLAY)
        await connection_manager.broadcast(GAMES_LIST_ID, f"{PULL_GAMES} {get_time()}")
        return utils.game_data_sample(game)

@app.patch("/{id_gamex}/{id_player}/{id_card}/{id_player_afected}", status_code=status.HTTP_200_OK)
async def play_card(id_gamex: int, id_player: int, id_card: int, id_player_afected: int) -> dict:
    """Plays a card
    Input:
        id_player_afected
    ---------
    Output: GameProgress
        Information about the game progress
    """
    with db_session:
        game = utils.validate_game(id_gamex)
        player = utils.validate_player(id_player)
        card = utils.validate_card(id_card, id_player)
        if card.name not in SINGLE_ARGUMENT_CARDS:
            player_afected = utils.validate_player(id_player_afected) # TODO: handle case where this is not needed

        if player.position != game.current_turn or game.turn_phase != Status.BEGIN:
            detail_message = f"You cannot play a card, {player.name}." + "\n"
            detail_message = detail_message + "Either it is not your turn, or not the right turn phase"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail_message
            )

        if card.kind != Kind.ACTION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_PLAY"
            )

        # TODO
        target_has_defense = False
        card_is_autoplay = True

        if (not target_has_defense) or card_is_autoplay:

            if card.name == CardName.FLAMETHROWER:
                mensaje = card_actions.play_flamethrower(game, player_afected)
                print(f"{player.name} jugó lanzallamas sobre {player_afected.name}")
            if card.name == CardName.WATCH_YOUR_BACK:
                mensaje = card_actions.play_watch_your_back(game)
                print(f"{player.name} jugó vigila tus espaldas")
            if card.name == CardName.SWAP_PLACES:
                mensaje = card_actions.swap_places(game, player, player_afected)
                print(f"{player.name} jugó cambio de lugar con {player_afected.name}")
            if card.name == CardName.YOU_BETTER_RUN:
                mensaje = card_actions.play_you_better_run(game, player ,player_afected)
                print(f"{player.name} jugó mejor que corras con {player_afected.name}")
            if card.name == CardName.SEDUCTION:
                mensaje = card_actions.play_seduction(player, player_afected)
            if card.name == CardName.ANALYSIS:
                mensaje = card_actions.show_cards_of_player(game, player_afected)
                print(f"{player.name} jugó analisis sobre {player_afected.name}")
            if card.name == CardName.WHISKY:
                mensaje = card_actions.show_cards_of_player(game, player)
                print(f"{player.name} jugó whiskey")
            if card.name == CardName.SUSPICION:
                mensaje = card_actions.show_single_card_to_player(player, player_afected)
                print(f"{player.name} jugó sospecha sobre {player_afected.name}")
            else:
                mensaje = f"A non existent card name was received when playing a card. Card name was -{card.name}-"

            utils.discard_card(game, player, card)
            #se hace acá para primer probar la funcionalidad sin intercamio de cartas
            game.turn_phase = Status.EXCHANGE_OFFER
            if game.going_clockwise:
                turn_shift = 1
            else:
                turn_shift = -1
            flush()
            player_offering = [p for p in game.players if p.position == game.current_turn].pop()
            player_responding = [p for p in game.players if p.position == (game.current_turn + turn_shift) % game.number_of_players].pop()
            print(f"{player_offering.name} intercambia {player_responding.name} responde a intercambio")
            # broadcast updated game state
            await connection_manager.trigger_game_update(id_gamex)
            utils.db_game_2_game_progress(game)
            return {"game_progress": utils.db_game_2_game_progress(game),
                    "message": mensaje}

        # TODO
        if target_has_defense:
            player.action = card.id
            player_afected.status = Status.ACTION_DEFENSE_REQUEST
            await connection_manager.trigger_game_update(id_gamex)
            pass

@app.patch("/exchange/choose/card/{game_id}/{player_id}/{card_id}", status_code=status.HTTP_200_OK)
async def exchange_offer(game_id: int, player_id: int, card_id: int) -> bool:
    with db_session:

        game = utils.validate_game(int(game_id)) # TODO
        player = utils.validate_player(int(player_id))
        card = utils.validate_card(int(card_id), int(player_id))

        if game.going_clockwise:
            turn_shift = 1
        else:
            turn_shift = -1

        player_is_offering = player.position == game.current_turn
        player_is_responding = player.position == (game.current_turn + turn_shift) % game.number_of_players
        player_is_target = player.id == game.current_target

        phase_is_offer = game.turn_phase == Status.EXCHANGE_OFFER
        phase_is_respond = game.turn_phase == Status.EXCHANGE_RESPONSE
        phase_is_seduction = game.turn_phase == Status.SEDUCTION_OFFER
        phase_is_seduction_response = game.turn_phase == Status.SEDUCTION_RESPONSE

        right_conditions = [
            (player_is_offering and phase_is_offer),
            (player_is_responding and phase_is_respond),
            (player_is_offering and phase_is_seduction),
            (player_is_target and phase_is_seduction_response)
        ]

        player_is_allowed = True in right_conditions

        if not player_is_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"It is not the time to offer a card exchange, {player.name}"
            )

        player_is_the_thing = player.role == Role.THING
        infection = card.name == CardName.INFECTED

        if infection and not player_is_the_thing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only the thing can exchange infection cards, {player.name}"
            )

        if infection:
            card.active_infection = True

        player.exchange_offer = card_id

        if player_is_offering and phase_is_offer:
            game.turn_phase = Status.EXCHANGE_RESPONSE
            await connection_manager.trigger_game_update(game_id)
            flush()
            return True

        if player_is_offering and phase_is_seduction:
            game.turn_phase = Status.SEDUCTION_RESPONSE
            await connection_manager.trigger_game_update(game_id)
            flush()
            return True

        if player_is_responding and (phase_is_respond or phase_is_seduction_response):

            turn = game.current_turn
            exchanger = [p for p in game.players if p.position == turn].pop()
            responder = player

            offer_id = exchanger.exchange_offer
            offer = [c for c in exchanger.hand if c.id == offer_id].pop()

            response = card
            exchanger.hand.add(response)
            responder.hand.add(offer)
            exchanger.hand.remove(offer)
            responder.hand.remove(response)

            if (exchanger.role == Role.THING and offer.name == CardName.INFECTED):
                responder.role = Role.INFECTED
            elif(responder.role == Role.THING and response.name == CardName.INFECTED):
                exchanger.role == Role.INFECTED

            if card.active_infection:
                responder.role = Role.INFECTED

            if utils.check_full_infection(game):
                print("Todos los jugadores estan infectados")
                game.is_done = True
                game.game_over_status = Role.THING
                flush()
                await connection_manager.trigger_game_update(game_id)
                return True

            utils.change_turn(game_id)
            player_turn = select(p for p in game.players if p.position == game.current_turn).first()
            print(f"Turno de {player_turn.name}")
            game.turn_phase = Status.BEGIN
            for p in game.players:
                if not p.reveals.is_empty():
                    p.reveals.clear()

            await connection_manager.trigger_game_update(game_id)

            flush()

            return True

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


@app.delete("/discard/{id_game}/{id_player}/{id_card}", status_code=status.HTTP_200_OK)
async def discard_card(id_game: int, id_player:int, id_card: int) -> bool:
    """Discards a card from player hand"""
    with db_session:
        game = utils.validate_game(id_game)
        player = utils.validate_player(id_player)
        if player.position != game.current_turn or game.turn_phase != Status.BEGIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="It is either not your turn, or you're not in discard phase, {player.name}"
                )
        card = utils.validate_card(id_card, id_player)

        if card.active_infection:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You cannot get rid of your infection, {player.name}!"
                )

        utils.discard_card(game, player, card)
        print(f"{player.name} descartó una carta")
        game.turn_phase = Status.EXCHANGE_OFFER
        flush()
        if game.going_clockwise:
            turn_shift = 1
        else:
            turn_shift = -1
        player_offering = [p for p in game.players if p.position == game.current_turn].pop()
        player_responding = [p for p in game.players if p.position == (game.current_turn + turn_shift) % game.number_of_players].pop()
        print(f"{player_offering.name} intercambia {player_responding.name} responde a intercambio")
        await connection_manager.trigger_game_update(id_game)
        return True

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

# TODO: frontend must allow players to set as defenses only the relevant cards
# TODO: when executing the effect of an interaction, some defenses have to be removed,
# and some do not
app.post("/defense/{game_id}/{player_id}/{card_id}", status_code=status.HTTP_200_OK)
async def add_defense(game_id:int, player_id: int, card_id: int):
    with db_session:
        player = utils.validate_player(player_id)
        card = utils.validate_card(card_id, player_id)
        player.defenses.add(card)
        utils.next_phase(game_id)
        flush()
    return True

@app.websocket("/ws/join")
async def websocket_join(websocket: WebSocket):
    user_id = await connection_manager.connect(GAMES_LIST_ID, websocket)
    await websocket.send_text("USER ID: " + str(user_id))
    connection_manager.user_state[user_id] = JOIN
    connection_manager.game_to_users[GAMES_LIST_ID].append(user_id)
    try:
        while True:
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)

@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(0, websocket)
    while True:
        try:
            sender = await connection_manager.get_chat_sender(websocket)
            await connection_manager.broadcast_chat_message(sender, chat.last())
            data = await websocket.receive_text()
            if data:
                chat.append(data)
        except WebSocketDisconnect:
            await connection_manager.disconnect(0, websocket)
            break

#Debug purposes
"""
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
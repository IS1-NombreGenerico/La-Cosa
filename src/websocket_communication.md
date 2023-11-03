# Websocket Communication
This file describes the communication between the server and the client via websockets using messages from different endpoints.

#### Endpoints and their messages
* start_game PATCH `"/{id_game}/{id_player}"`:
    
    message: `"event": "draw_card", "player_name": ...}`

    The player name who start the game.

    Sended to all player in same game.

* start_exchange POST `"/{id_game}/{id_player}/{id_card}/start_exchange"`:

    message: `{"event": "exchange_card", "player_name": ...}`

    `player_name` : str

    The player name who have to respond to the exchange.

    Sended to all player in same game.

* complete_exchange POST `"/{id_game}/{id_player}/{id_card}/end_exchange"`:

    message: `"event": "draw_card", "player_name": ...}`

    The player name who have the next turn.

    Sended to all player in same game.




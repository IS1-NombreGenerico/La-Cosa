import json
from typing import DefaultDict
from collections import defaultdict

from fastapi import WebSocket

from schemas import GameInDB, GameOut

class ConnectionManager:
    # General Methods

    def __init__(self) -> list[(int, WebSocket)]:
        self.active_connections: DefaultDict[int, list[WebSocket]] = defaultdict(lambda: [])
        self.connection_players: DefaultDict[WebSocket, tuple[int, int]] = {}
    
    async def connect(self, game_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[game_id].append(websocket)

    def disconnect(self, game_id: int, websocket: WebSocket) -> None:
        for socket in self.active_connections[game_id]:
            if socket == websocket:
                self.active_connections[game_id].remove(websocket)

    async def get_websocket(self, game_id: int, player_id: int) -> WebSocket:
        for conn in self.active_connections[game_id]:
            if self.connection_players[conn] == (game_id, player_id):
                return conn
        raise Exception("Connection not found")
    
    async def set_websocket(self, game_id: int, player_id: int, websocket: WebSocket) -> None:
        self.connection_players[websocket] = (game_id, player_id)

    async def delete_websocket(self, websocket: WebSocket) -> None:
        del self.connection_players[websocket]
    
    async def send_personal_message(self, game_id: int, message: str, websocket: WebSocket) -> None:
        for conn in self.active_connections[game_id]:
            if conn == websocket:
                await websocket.send_text(message)
                break

    async def broadcast(self, game_id: int, message: str) -> None:
        for conn in self.active_connections[game_id]:
            await conn.send_text(message)
    
    async def join_game(self, game_id: int, websocket: WebSocket, player_id: int) -> None:
        self.connection_players[websocket] = (game_id, player_id)
        await self.connect(game_id, websocket)

    # Methods for listing games ("/join") communication

    async def send_games(self, games: list[GameOut]) -> None:
        games_list_id = 0
        games_json = json.dumps([g.__dict__ for g in games])
        await self.broadcast(games_list_id, games_json)
    
    # Method for lobby ("join/{game_id}")communication

    async def send_lobby_info(self, game_id: int, game_info: GameInDB) -> None:
        game_info_json = json.dumps(game_info.__dict__)
        await self.broadcast(game_id, game_info_json)

    async def move_connection(self, current_game_id: int, target_game_id: int, websocket: WebSocket):
        if current_game_id in self.active_connections and target_game_id in self.active_connections:
            if websocket in self.active_connections[current_game_id]:
                self.active_connections[current_game_id].remove(websocket)
                self.active_connections[target_game_id].append(websocket)
            else:
                raise Exception("Connection not found in the current game")
        else:
            raise Exception("Invalid current or target game ID")

    async def remove_all_connection_of_game(self, game_id: int) -> None:
        if game_id in self.active_connections:
            for conn in self.active_connections[game_id]:
                await self.move_connection(game_id, 0, conn)
                await self.delete_websocket(conn)
            del self.active_connections[game_id]
        else:
            raise Exception("Invalid game ID")

""" class CollaborationManager:

    def __init__(self) -> None:
        self.collaboration_data: DefaultDict[int, tuple[dict, dict]] = defaultdict(lambda: ({}, {}))
    
    def add_collaboration1(self, game_id: int, data: dict) -> None:
        self.collaboration_data[game_id][player1] = data """
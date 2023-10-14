import json
from typing import DefaultDict
from collections import defaultdict

from fastapi import WebSocket

from schemas import GameInDB, GameOut

class ConnectionManager:
    # General Methods

    def __init__(self) -> list[(int, WebSocket)]:
        self.active_connections: DefaultDict[int, list[WebSocket]] = defaultdict(lambda: [])
    
    async def connect(self, game_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[game_id].append(websocket)

    def disconnect(self, game_id: int, websocket: WebSocket) -> None:
        for socket in self.active_connections[game_id]:
            if socket == websocket:
                self.active_connections[game_id].remove(websocket)
    
    async def send_personal_message(self, game_id: int, message: str, websocket: WebSocket) -> None:
        for conn in self.active_connections[game_id]:
            if conn == websocket:
                await websocket.send_text(message)
                break

    async def broadcast(self, game_id: int, message: str) -> None:
        for conn in self.active_connections[game_id]:
            await conn.send_text(message)

    # Methods for listing games ("/join") communication

    async def send_games(self, games: list[GameOut]) -> None:
        games_list_id = 0
        games_json = json.dumps([g.__dict__ for g in games])
        await self.broadcast(games_list_id, games_json)
    
    # Method for lobby ("join/{game_id}")communication

    async def send_lobby_info(self, game_id: int, game_info: GameInDB) -> None:
        game_info_json = json.dumps(game_info.__dict__)
        await self.broadcast(game_id, game_info_json)

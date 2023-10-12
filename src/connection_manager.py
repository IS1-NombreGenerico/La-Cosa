from fastapi import WebSocket
import json

from schemas import GameInDB, GameOut

class ConnectionManager:
    # General Methods

    def __init__(self) -> list[(int, WebSocket)]:
        self.active_connections: list[(int, WebSocket)] = []
    
    async def connect(self, game_id: int ,websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append((game_id, websocket))

    def disconnect(self, websocket: WebSocket) -> None:
        for _, conn in self.active_connections:
            if conn == websocket:
                self.active_connections.remove(websocket)
                break
    
    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        for _, conn in self.active_connections:
            if conn == websocket:
                await websocket.send_text(message)
                break

    async def broadcast(self, game_id: int ,message: str) -> None:
        for game_id, conn in self.active_connections:
            if game_id == game_id:
                await conn.send_text(message)

    # Methods for listing games ("/join") communication

    async def send_games(self, games: list[GameOut]) -> None:
        games_json = json.dumps([g.__dict__ for g in games])
        await self.broadcast(0, games_json)
    
    # Method for lobby ("join/{game_id}")communication

    async def send_lobby_info(self, game_id: int, game_info: GameInDB) -> None:
        game_info_json = json.dumps(game_info.__dict__)
        await self.broadcast(game_id, game_info_json)
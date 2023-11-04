from typing import DefaultDict
from collections import defaultdict
import datetime

from fastapi import WebSocket

from messages import *

def get_time():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

class ConnectionManager:
    # General Methods

    def __init__(self) -> list[(int, WebSocket)]:
    
        self.user_sockets : dict[int, WebSocket] = {}
        self.user_state: dict[int, str] = {}
        self.socket_to_player : dict[int, int] = {}
        self.player_to_socket : dict[int, int] = {}
        self.player_to_game : dict[int, int] = {}
        self.game_to_users : DefaultDict[int, list[int]] = defaultdict(lambda : [])
        self.current_id : int = 0
    
    async def connect(self, game_id: int, websocket: WebSocket) -> int:
        await websocket.accept()
        self.current_id += 1
        self.user_sockets[self.current_id] = websocket
        return self.current_id

    async def disconnect(self, socket_id: int) -> None:
        del self.user_sockets[socket_id]
    
    async def send_personal_message(self, socket_id : int, message : str) -> None:
        await self.user_sockets[socket_id].send_text(message)

    async def broadcast(self, game_id: int, message: str) -> None:
        for user_id in self.game_to_users[game_id]:
            await self.user_sockets[user_id].send_text(message)
            
    async def move_user(self, user_id: int, source: int, target: int, state: str) -> None:
        if user_id in self.game_to_users[source]:
            self.game_to_users[source].remove(user_id)
        if user_id in self.socket_to_player and target == 0:
            socket_player = self.socket_to_player[user_id]
            del self.socket_to_player[user_id]
            del self.player_to_socket[socket_player]
        self.game_to_users[target].append(user_id)
        await self.broadcast(0, f"{PULL_GAMES} {get_time()}")
        await self.broadcast(source, f"{UPDATE_GAME} {get_time()}")
        await self.broadcast(target, f"{UPDATE_GAME} {get_time()}")
        self.user_state[user_id] = state
        
            

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
        self.game_to_users : DefaultDict[int, list[int]] = defaultdict(lambda : [])
        self.user_to_game : DefaultDict[int, int] = defaultdict(lambda : [])
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

    async def get_chat_sender(self, socket: WebSocket) -> int:
        for user_id, user_socket in self.user_sockets.items():
            if user_socket == socket:
                return user_id

    async def broadcast_chat_message(self, sender: int, message: str) -> None:
        for user_id in self.game_to_users[self.user_to_game[sender]]:
            await self.user_sockets[user_id].send_text(message)

    async def trigger_game_update(self, game_id: int) -> None:
        await self.broadcast(game_id, f"{UPDATE_GAME} {get_time()}")

    async def move_user(self, user_id: int, source: int, target: int, state: str) -> None:
        if user_id in self.game_to_users[source]:
            self.game_to_users[source].remove(user_id)
        self.game_to_users[target].append(user_id)
        self.user_to_game[user_id] = target
        await self.broadcast(0, f"{PULL_GAMES} {get_time()}")
        await self.broadcast(source, f"{UPDATE_GAME} {get_time()}")
        await self.broadcast(target, f"{UPDATE_GAME} {get_time()}")
        self.user_state[user_id] = state

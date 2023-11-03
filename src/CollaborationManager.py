from typing import DefaultDict
from collections import defaultdict

class CollaborationManager:
    """Class to hold data between different endpoints"""

    def __init__(self) -> None:
        self.collaboration_data: DefaultDict[int, tuple[dict, dict]] = defaultdict(lambda: ({}, {}))

    def init_buffer(self, game_id: int) -> None:
        self.collaboration_data[game_id] = ({}, {})

    def add_first_collaboration(self, game_id: int, data: dict) -> None:
        self.collaboration_data[game_id]["player1"] = data

    def add_second_collaboration(self, game_id: int, data: dict) -> None:
        self.collaboration_data[game_id]["player2"] = data

    def get_just_p1_data(self, game_id: int) -> dict:
        data = self.collaboration_data[game_id]["player1"]
        self.collaboration_data[game_id] = ({}, {})
        return data

    def get_data(self, game_id: int) -> tuple[dict, dict]:
        data = self.collaboration_data[game_id]
        self.collaboration_data[game_id] = ({}, {})
        return data
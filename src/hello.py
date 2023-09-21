from fastapi import FastAPI
from entities import (Card, Player, Game, db)
from schemas import CreateGameIn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/game")
async def create_game(form: CreateGameIn) -> CreateGameIn:
    return form
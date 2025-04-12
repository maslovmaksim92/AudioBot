from fastapi import FastAPI
from app.api import bot

app = FastAPI(title="AudioBot")

@app.get("/")
def root():
    return {"status": "ok"}

app.include_router(bot.router)
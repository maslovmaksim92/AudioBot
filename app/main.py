from fastapi import FastAPI
from app.api import bot

app = FastAPI(title="AudioBot")

app.include_router(bot.router)
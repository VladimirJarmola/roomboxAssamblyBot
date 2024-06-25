from fastapi import FastAPI, Request
from app import bot

app = FastAPI()

@app.post('/api/bot')
async def tgbot_webhook_route(request: Request):
    update_dict = await request.json()
    await bot.update_bot(update_dict)
    return 'Hello'
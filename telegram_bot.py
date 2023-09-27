import json
import logging
import os
from typing import List

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

from src.Dtos import GameDetailDto
from src.Json import read_json
from src.Utils import get_current_folder

token = os.getenv("BOT_TOKEN")


class Chats:
    def __init__(self, path: str):
        self.path = path
        self.chats = set()
        self.update()

    def update(self):
        if not os.path.exists(self.path):
            return

        with open(self.path, "r") as f:
            self.chats = set(json.load(f))

    def add(self, chat_id: int):
        with open(self.path, "w+") as f:
            self.chats.add(chat_id)
            json.dump(list(self.chats), f)
        self.update()

    def remove(self, chat_id: int):
        with open(self.path, "w+") as f:
            self.chats.remove(chat_id)
            json.dump(list(self.chats), f)
        self.update()


chats = Chats("./data/chats.json")
sent_bet365 = False
sent_pinnacle = False
sent_dafabet = False

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Use /register or /unregister to subscribe to new lol games",
    )


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chats.add(update.effective_chat.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Added chat to subscribed chats"
    )


async def unregister(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chats.remove(update.effective_chat.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Removed chat to subscribed chats"
    )


def get_games(section: str) -> List[GameDetailDto]:
    print(f"{get_current_folder()}/games_{section}Webscraper.json")
    return read_json(f"{get_current_folder()}/games_{section}Webscraper.json")


async def send_updates(context: ContextTypes.DEFAULT_TYPE):
    global sent_bet365, sent_dafabet, sent_pinnacle
    bet365 = get_games("Bet365")
    pinnacle = get_games("Pinnacle")
    dafabet = get_games("Dafabet")

    scrapers = []
    if not sent_bet365 and len(bet365) != 0:
        sent_bet365 = True
        scrapers.append(bet365)
    if not sent_dafabet and len(dafabet) != 0:
        sent_dafabet = True
        scrapers.append(dafabet)
    if not sent_pinnacle and len(pinnacle) != 0:
        sent_pinnacle = True
        scrapers.append(pinnacle)

    for scraper in scrapers:
        messages = [f"New game added\n\n{dto.pretty_print()}" for dto in scraper]
        for chat in chats.chats:
            for msg in messages:
                await context.bot.send_message(chat_id=chat, text=msg)

    if sent_dafabet and sent_bet365 and sent_pinnacle:
        exit(1)


if __name__ == "__main__":
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("unregister", unregister))

    job_queue = application.job_queue

    job_minute = job_queue.run_repeating(send_updates, interval=60, first=10)
    application.run_polling()

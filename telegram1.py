import csv
from telegram import Bot
import asyncio
import logging

TOKEN = '6475025056:AAE1jWC2aHVMpZVBAyAjFumimwnyTG2iuQo'
CHAT_ID = '1142829842'
CSV_FILE_PATH = 'bets\\bets.csv'
LOG_FILE = 'logs/telegram_bot.log'

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

# Suppress unwanted HTTP logs from the Telegram library
all_loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
for logger in all_loggers:
    if logger is not logging.root:
        logger.setLevel(logging.ERROR)

async def send_message(text, csv_line):
    # Check if this CSV line was sent before
    if not is_line_logged(csv_line):
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text)
        log_line(csv_line)

def is_line_logged(csv_line):
    with open(LOG_FILE, 'r') as file:
        content = file.read()
        return csv_line in content

def log_line(csv_line):
    logging.info(csv_line)

MAX_RETRIES = 3

async def watch_csv_file():
    last_line_count = 0
    retries = 0  # Keep track of how many times no new lines were found

    while True:
        with open(CSV_FILE_PATH, 'r') as file:
            lines = file.readlines()

            # Skip the header if this is the first time reading the file
            if last_line_count == 0:
                last_line_count = 1

            if len(lines) > last_line_count:
                # New line(s) added
                for new_line in lines[last_line_count:]:
                    csv_data = list(csv.reader([new_line]))
                    formatted_message = format_csv_data_to_message(csv_data[0])
                    await send_message(formatted_message, new_line.strip())
                last_line_count = len(lines)
                retries = 0  # Reset retries if new lines are found
            else:
                retries += 1
                if retries >= MAX_RETRIES:
                    print("No new lines detected for the past checks. Exiting...")
                    break

        await asyncio.sleep(10)

def format_csv_data_to_message(row):
    # Format the CSV row data to the TIP message for Telegram
    message = (f"New Bet Added!\n"
               f"📅 Date: {row[0]}\n"
               f"🏆 League: {row[1]}\n"
               f"🥇 Team 1: {row[2]}\n"
               f"🥈 Team 2: {row[3]}\n\n"
               f"🎲 TIP: {row[4]} - {row[5]}\n"
               f"📊 ROI: {row[6]}\n"
               f"🔢 Odds: {row[7]}\n"
               f"🏠 Betting House: {row[8]}")
    return message

if __name__ == "__main__":
    asyncio.run(watch_csv_file())

import os
import pandas as pd
from telegram import Bot
import asyncio
import logging
from datetime import datetime
import pyshorteners
from dotenv import load_dotenv

# Configuration Constants
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
# TOKEN = '6475025056:AAE1jWC2aHVMpZVBAyAjFumimwnyTG2iuQo'
# CHAT_ID = -1002032762903
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE_PATH = os.path.join(BASE_DIR, '..', 'bets', 'bets.csv')
BET_TRACK_PATH = os.path.join(BASE_DIR, 'new_bot.csv')
MESSAGE_DELAY = 2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def shorten_url(url):
    if not url.startswith(("http://", "https://")):
        return ""
    try:
        return pyshorteners.Shortener().tinyurl.short(url)
    except Exception as e:
        logging.error(f"Error shortening URL {url}: {e}")
        return url

def create_unique_identifier(row_or_df):
    columns_to_use = ['date', 't1', 't2', 'bet_type', 'bet_line', 'House']
    if isinstance(row_or_df, pd.Series):
        return '_'.join(row_or_df[columns_to_use].astype(str))
    elif isinstance(row_or_df, pd.DataFrame):
        # Create a copy to avoid SettingWithCopyWarning
        df_copy = row_or_df.copy()
        df_copy['identifier'] = df_copy[columns_to_use].astype(str).agg('_'.join, axis=1)
        return df_copy


def filter_untracked_bets(bets_df, track_df):
    # Add identifiers to both DataFrames
    bets_df = create_unique_identifier(bets_df)
    track_df = create_unique_identifier(track_df)

    # Efficient filtering using boolean indexing
    filtered_bets = bets_df[~bets_df['identifier'].isin(track_df['identifier'])]
    return filtered_bets

async def process_bet_group(group):
    message = consolidate_messages(group)
    await send_message(CHAT_ID, message)
    for _, bet in group.iterrows():
        update_tracking_file(bet, 'sent')

async def process_grouped_bets(bets_df):
    if not bets_df.empty:
        grouped_bets = bets_df.groupby(['date', 't1', 't2', 'House'])
        for _, group in grouped_bets:
            await process_bet_group(group)

async def process_changed_bets(changed_bets_df, track_df):
    changed_bets_df = create_unique_identifier(changed_bets_df)
    track_df = create_unique_identifier(track_df)

    # Filter out bets that are already tracked
    filtered_changed_bets = changed_bets_df[~changed_bets_df['identifier'].isin(track_df['identifier'])]

    for _, bet in filtered_changed_bets.iterrows():
        # Process each changed bet
        update_message = format_bet_message(bet)
        await send_message(CHAT_ID, update_message)
        update_tracking_file(bet, bet['status'], 1)

def format_bet_message(bet):
    return (
        f"📅 Date: {bet['date']}\n"
        f"🏆 League: {bet['league']}\n"
        f"🥇 Team 1: {bet['t1']} vs 🥈 Team 2: {bet['t2']}\n"
        f"🎲 Bet Type: {bet['bet_type']} - {bet['bet_line']}\n"
        f"📊 ROI: {bet['ROI']} | Fair Odds: {bet['fair_odds']}\n"
        f"🔢 Odds: {bet['odds']}\n"
        f"🏠 Betting House: {bet['House']}\n"
        f"🔗 {shorten_url(bet['url']) if 'url' in bet and bet['url'] else 'No URL'}"
    )

def consolidate_messages(bets):
    # Consolidate messages for bets with the same date, t1, t2, and betting house
    messages = []
    for _, bet in bets.iterrows():
        messages.append(format_bet_message(bet))
    return "\n\n".join(messages)

async def send_message(chat_id, text):
    bot = Bot(token=TOKEN)
    try:
        await bot.send_message(chat_id, text, disable_web_page_preview=True)
        await asyncio.sleep(MESSAGE_DELAY)
    except Exception as e:
        logging.error(f"Error sending message: {e}")

def read_csv(filepath, default_columns):
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return pd.DataFrame(columns=default_columns)
    try:
        return pd.read_csv(filepath)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=default_columns)
    
def update_tracking_file(bet, new_status, settlement_sent=0):
    default_columns = ['date', 'league', 't1', 't2', 'bet_type', 'bet_line', 'ROI', 'fair_odds', 'odds', 'House', 'url', 'status', 'settlement_sent']
    track_df = read_csv(BET_TRACK_PATH, default_columns)
    bet_id = create_unique_identifier(bet)

    if settlement_sent == 0:
        new_bet = pd.DataFrame([bet], columns=default_columns)
        new_bet['settlement_sent'] = settlement_sent
        track_df = pd.concat([track_df, new_bet], ignore_index=True)
    else:
        # Add the bet to the tracking file with the new 'tracked_status'
        track_df.loc[track_df.apply(create_unique_identifier, axis=1) == bet_id, 'status'] = new_status
        track_df.loc[track_df.apply(create_unique_identifier, axis=1) == bet_id, 'settlement_sent'] = settlement_sent
    try:
        track_df.to_csv(BET_TRACK_PATH, index=False)
    except Exception as e:
        logging.error(f"Error updating tracking file: {e}", exc_info=True)

async def process_bets():
    bets_df = read_csv(CSV_FILE_PATH, ['date', 'league', 't1', 't2', 'bet_type', 'bet_line', 'ROI', 'fair_odds', 'odds', 'House', 'url', 'status'])
    track_df = read_csv(BET_TRACK_PATH, ['date', 'league', 't1', 't2', 'bet_type', 'bet_line', 'ROI', 'fair_odds', 'odds', 'House', 'url', 'status', 'settlement_sent'])

    # Process Pending Bets
    pending_bets_df = filter_untracked_bets(bets_df[bets_df['status'] == 'pending'], track_df)   
    await process_grouped_bets(pending_bets_df)

    # Process Settled Bets
    changed_bets_df = bets_df[bets_df['status'].isin(['win', 'loss'])]
    await process_changed_bets(changed_bets_df, track_df)

async def main():
    try:
        await process_bets()
    except Exception as e:
        logging.exception("An unhandled error occurred in the main function")

if __name__ == "__main__":
    asyncio.run(main())

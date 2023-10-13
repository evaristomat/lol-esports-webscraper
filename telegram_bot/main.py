import csv
import os
import pandas as pd
from telegram import Bot
import asyncio
import logging
from datetime import datetime

TOKEN = '6475025056:AAE1jWC2aHVMpZVBAyAjFumimwnyTG2iuQo'
CHAT_ID = '1142829842'
CSV_FILE_PATH = '../bets/bets.csv'
BET_TRACK_PATH = 'bet_track.csv'
LOG_FILE = '../logs/telegram_bot.log'

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

# Global flag to check if messages were sent
MESSAGES_SENT = False

def safe_read_csv(filepath):
    columns_for_bet_track = ["date", "league", "t1", "t2", "bet_type", "bet_line", "ROI", 
                             "fair_odds", "odds", "House", "status", "settled", "message_sent"]  # Added "message_sent" column
    try:
        if not (os.path.exists(filepath) and os.path.getsize(filepath) > 0):
            if filepath == BET_TRACK_PATH:
                empty_df = pd.DataFrame(columns=columns_for_bet_track)
                empty_df['message_sent'] = empty_df['message_sent'].astype(int)
                empty_df.to_csv(filepath, index=False)
            return None
        return pd.read_csv(filepath)
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return None


def log_line(row_data):
    """Add a new row to bet_track.csv."""
    df = safe_read_csv(BET_TRACK_PATH)
    if df is not None:
        # Add message_sent status to the row_data
        row_data['message_sent'] = 1
        
        new_df = pd.DataFrame([row_data])  # Create a new DataFrame from the row_data
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(BET_TRACK_PATH, index=False)


def update_message_sent_status(bet_row):
    """
    Update the message_sent status in bet_track.csv to indicate the message has been sent.
    """
    df = safe_read_csv(BET_TRACK_PATH)
    
    conditions = (df['date'] == bet_row['date']) & \
                 (df['league'] == bet_row['league']) & \
                 (df['t1'] == bet_row['t1']) & \
                 (df['t2'] == bet_row['t2']) & \
                 (df['bet_type'] == bet_row['bet_type']) & \
                 (df['bet_line'] == bet_row['bet_line'])
    
    df.loc[conditions, 'message_sent'] = 1
    df.to_csv(BET_TRACK_PATH, index=False)

def update_settled_status(bet_row, settled_status):
    """
    Update the 'settled' status in bet_track.csv.
    """
    df = safe_read_csv(BET_TRACK_PATH)
    
    conditions = (df['date'] == bet_row['date']) & \
                 (df['league'] == bet_row['league']) & \
                 (df['t1'] == bet_row['t1']) & \
                 (df['t2'] == bet_row['t2']) & \
                 (df['bet_type'] == bet_row['bet_type']) & \
                 (df['bet_line'] == bet_row['bet_line'])
    
    df.loc[conditions, 'settled'] = settled_status
    df.to_csv(BET_TRACK_PATH, index=False)

def is_message_sent(bet_row, track_df):
    is_sent = track_df[
        (track_df['date'] == bet_row['date']) &
        (track_df['league'] == bet_row['league']) &
        (track_df['t1'] == bet_row['t1']) &
        (track_df['t2'] == bet_row['t2']) &
        (track_df['bet_type'] == bet_row['bet_type']) &
        (track_df['bet_line'] == bet_row['bet_line']) &
        (track_df['message_sent'] == 1)  # Check if the message for this bet has been sent
    ].any(axis=1).any()

    return is_sent

def is_bet_processed(row_data):
    """Check if a bet is already tracked in bet_track.csv."""
    df = safe_read_csv(BET_TRACK_PATH)  # Update path here
    tracked_bets = df[
        (df.date == row_data['date']) &
        (df.league == row_data['league']) &
        (df.t1 == row_data['t1']) &
        (df.t2 == row_data['t2']) &
        (df.bet_type == row_data['bet_type']) &
        (df.bet_line == row_data['bet_line']) &
        (df.tracked == 1)
    ]
    return not tracked_bets.empty

def compare_bet_status():
    # Read both CSV files
    df_bets = safe_read_csv(CSV_FILE_PATH)
    df_track = safe_read_csv(BET_TRACK_PATH)

    # Merge on columns of interest (assuming 'date', 'league', 't1', and 't2' uniquely identify a bet)
    merged = pd.merge(df_bets, df_track, on=['date',
                                             'league',
                                             't1',
                                             't2', 'bet_type', 'bet_line'], suffixes=('', '_tracked'))

    # Find rows where status has changed
    changed_bets = merged[merged['status'] != merged['status_tracked']]

    # Return the changed bets for further processing
    return changed_bets

async def send_message(text, row_data, status="pending"):
    global MESSAGES_SENT
    
    bot = Bot(token=TOKEN)
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
        MESSAGES_SENT = True

        # Update the tracked status in the CSV based on the status
        update_message_sent_status(row_data)
    except Exception as e:
        print(f"Error sending message or updating bet_track.csv: {e}")

async def process_pending_bets():
    df_bets = safe_read_csv(CSV_FILE_PATH)
    df_track = safe_read_csv(BET_TRACK_PATH)
    pending_bets = df_bets[df_bets['status'] == 'pending']

    for _, bet in pending_bets.iterrows():
        row_data = bet.to_dict()
        if not is_message_sent(row_data, df_track):
            message = format_csv_data_to_message(bet)
            print("Bet Added!")
            await send_message(message, row_data)
            row_data['settled'] = 0  # Mark bet as not settled
            log_line(row_data)

async def process_changed_bets():
    changed_bets = compare_bet_status()
    for _, bet in changed_bets.iterrows():
        row_data = bet.to_dict()
        message = format_csv_data_to_message(bet, bet['status'])
        await send_message(message, row_data, bet['status'])
        
        # Update the 'settled' status to 1 (since the bet has been processed)
        update_settled_status(row_data, 1)

def get_daily_summary():
    df = safe_read_csv(CSV_FILE_PATH)
    
    # Get the current date in the format 'YYYY-MM-DD'
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Filter the dataframe for the current date
    df = df[df['date'] == current_date]
    
    # Count the wins and losses
    wins = len(df[df['status'] == 'win'])
    losses = len(df[df['status'] == 'loss'])
    
    # Calculate the profit/loss
    df['profit'] = df.apply(lambda x: x['odds'] - 1 if x['status'] == 'win' else -1 if x['status'] == 'loss' else 0, axis=1)
    profit = df['profit'].sum()

    # Format the summary
    summary = (f"📊 *Daily Summary for {current_date}:*\n"
               f"✅ *Wins:* {wins}\n"
               f"❌ *Losses:* {losses}\n"
               f"💰 *Profit:* {profit:.2f}")
    
    return summary

async def send_daily_summary():
    summary = get_daily_summary()
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=summary, parse_mode='Markdown')

def get_monthly_summary():
    # Read the CSV using pandas
    df = safe_read_csv(CSV_FILE_PATH)
    
    # Get the current month in the format 'Month - Year' (e.g., 'October - 2023')
    current_month = datetime.now().strftime('%B - %Y')
    
    # Filter the dataframe for the current month
    df = df[df['date'].str.startswith(current_month.split(' - ')[1] + '-' + datetime.now().strftime('%m'))]
    
    # Count the wins and losses
    wins = len(df[df['status'] == 'win'])
    losses = len(df[df['status'] == 'loss'])
    
    # Calculate the profit/loss
    df['profit'] = df.apply(lambda x: x['odds'] - 1 if x['status'] == 'win' else -1 if x['status'] == 'loss' else 0, axis=1)
    profit = df['profit'].sum()

    # Format the summary
    summary = (f"📊 *Monthly Summary for {current_month}:*\n"
               f"✅ *Wins:* {wins}\n"
               f"❌ *Losses:* {losses}\n"
               f"💰 *Profit:* {profit:.2f}")
    
    return summary

async def send_monthly_summary():
    summary = get_monthly_summary()
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=summary, parse_mode='Markdown')


MAX_RETRIES = 1

def format_csv_data_to_message(row, status="pending"):
    # Emoji based on status
    emoji = "✅" if status == "win" else "❌" if status == "loss" else ""
    prefix = "Bet Won!" if status == "win" else "Bet Lost!" if status == "loss" else "New Bet Added!"

    message = (f"{prefix} {emoji}\n"
               f"📅 Date: {row['date']}\n"
               f"🏆 League: {row['league']}\n"
               f"🥇 Team 1: {row['t1']}\n"
               f"🥈 Team 2: {row['t2']}\n\n"
               f"🎲 TIP: {row['bet_type']} - {row['bet_line']}\n"
               f"📊 ROI: {row['ROI']}\n"
               f"📉 Fair Odds: {row['fair_odds']}\n"
               f"🔢 Odds: {row['odds']}\n"
               f"🏠 Betting House: {row['House']}")
    return message

async def main():
    await process_pending_bets()
    await process_changed_bets()
    
    # Send monthly summary if any messages were sent
    if MESSAGES_SENT:
        await send_daily_summary()
        await send_monthly_summary()

if __name__ == "__main__":
    asyncio.run(main())
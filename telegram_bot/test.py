import csv
import os
import pandas as pd
from telegram import Bot
import asyncio
import logging
from datetime import datetime
import pyshorteners

TOKEN = '6475025056:AAE1jWC2aHVMpZVBAyAjFumimwnyTG2iuQo'
CHAT_ID = '1142829842'

# Get the directory of the script
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CSV_FILE_PATH = os.path.join(BASE_DIR, '..', 'bets', 'bets.csv')
BET_TRACK_PATH = os.path.join(BASE_DIR, 'bet_track.csv')


# Global flag to check if messages were sent
MESSAGES_SENT = False

def shorten_url(url):
    s = pyshorteners.Shortener()
    if isinstance(url, str) and url.startswith(("http://", "https://")):
        return s.tinyurl.short(url)
    else:
        return ""


def safe_read_csv(filepath):
    if filepath == BET_TRACK_PATH:
        columns_for_bet_track = ["date", "league", "t1", "t2", "bet_type", "bet_line", "ROI", 
                                "fair_odds", "odds", "House", "status", "message_sent", "settled","settlement_sent"]
        try:
            if not (os.path.exists(filepath) and os.path.getsize(filepath) > 0):
                empty_df = pd.DataFrame(columns=columns_for_bet_track)
                empty_df['message_sent'] = empty_df['message_sent'].astype(int)
                empty_df.to_csv(filepath, index=False)
                return empty_df
            return pd.read_csv(filepath)
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return None
    else:  # For all other CSVs
        try:
            if not (os.path.exists(filepath) and os.path.getsize(filepath) > 0):
                return None
            return pd.read_csv(filepath)
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return None

def filter_bets(df, bet_row):
    """Utility function to filter bets based on provided columns."""
    filtered = df
    for col in ['date', 'league', 't1', 't2', 'bet_type', 'bet_line']:
        if col not in df.columns:
            return pd.DataFrame()
        filtered = filtered[filtered[col] == bet_row[col]]
    return filtered

def update_or_log_bet_status(bet_row, mode="log"):
    df = safe_read_csv(BET_TRACK_PATH)
    
    conditions = (df['date'] == bet_row['date']) & \
                 (df['league'] == bet_row['league']) & \
                 (df['t1'] == bet_row['t1']) & \
                 (df['t2'] == bet_row['t2']) & \
                 (df['bet_type'] == bet_row['bet_type']) & \
                 (df['bet_line'] == bet_row['bet_line'])
    
    if mode == "log":
        bet_row['message_sent'] = 1
        bet_row['settled'] = 0        
        bet_row['settlement_sent'] = 0
        new_df = pd.DataFrame([bet_row])
        df = pd.concat([df, new_df], ignore_index=True)
    elif mode == "update_message":
        df.loc[conditions, 'message_sent'] = 1
    elif mode == "settle":
        df.loc[conditions, 'settled'] = 1
        df.loc[conditions, 'settlement_sent'] =1
    
    df.to_csv(BET_TRACK_PATH, index=False)

async def send_message(text, row_data, status="pending"):
    global MESSAGES_SENT
    
    bot = Bot(token=TOKEN)
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text, disable_web_page_preview=True)  # Disable link previews here
        MESSAGES_SENT = True
        update_or_log_bet_status(row_data, "update_message")
    except Exception as e:
        print(f"Error sending message: {e}")


async def process_bets(mode):
    df_bets = safe_read_csv(CSV_FILE_PATH)
    df_track = safe_read_csv(BET_TRACK_PATH)
    
    if mode == "pending":
        bets = df_bets[df_bets['status'] == 'pending']
        for _, bet in bets.iterrows():
            filtered_bets = filtered_bets = filter_bets(df_track, bet)
            if not filtered_bets.empty and filtered_bets['message_sent'].iloc[0] == 1:
                continue
            message = format_csv_data_to_message(bet)
            await send_message(message, bet.to_dict())
            update_or_log_bet_status(bet.to_dict())

    elif mode == "changed":
        changed_bets = pd.merge(df_bets, df_track, on=['date', 'league', 't1', 't2', 'bet_type', 'bet_line'], suffixes=('', '_tracked'))
        changed_bets = changed_bets[changed_bets['status'] != changed_bets['status_tracked']]
        print(changed_bets['url'])
        for _, bet in changed_bets.iterrows():
            if bet['settled'] == 1:
                continue
            #print(bet)
            message = format_csv_data_to_message(bet, bet['status'])
            await send_message(message, bet.to_dict(), bet['status'])
            update_or_log_bet_status(bet.to_dict(), "settle")


def format_csv_data_to_message(row, status="pending"):
    # Emoji and unit change based on status
    if status == "win":
        emoji = "✅"
        unit_change = f"+{row['odds'] -1:.2f}u"
    elif status == "loss":
        emoji = "❌"
        unit_change = "-1u"
    else:
        emoji = ""
        unit_change = "1u"

    prefix = f"Bet Won! {unit_change}" if status == "win" else \
             f"Bet Lost! {unit_change}" if status == "loss" else \
             f"New Bet Added! {unit_change}"
    
    shortened_url = shorten_url(row['url'])

    message = (f"{prefix} {emoji}\n"
               f"📅 Date: {row['date']}\n"
               f"🏆 League: {row['league']}\n"
               f"🥇 Team 1: {row['t1']}\n"
               f"🥈 Team 2: {row['t2']}\n\n"
               f"🎲 TIP: {row['bet_type']} - {row['bet_line']}\n"
               f"📊 ROI: {row['ROI']}\n"
               f"📉 Fair Odds: {row['fair_odds']}\n"
               f"🔢 Odds: {row['odds']}\n"
               f"🏠 Betting House: {row['House']}\n"
               f"🔗 {shortened_url}")
    return message

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
               f"💰 *Profit:* {profit:.2f} units")
    
    return summary

async def send_summary(mode="daily"):
    if mode == "daily":
        summary_msg = get_daily_summary()
    else:  # Assumes mode == "monthly"
        summary_msg = get_monthly_summary()
    
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=summary_msg, parse_mode='Markdown')


def get_monthly_summary():
    df = safe_read_csv(CSV_FILE_PATH)
    current_month = datetime.now().strftime('%B - %Y')
    
    # Filter for the current month
    df = df[df['date'].str.startswith(current_month.split(' - ')[1])]  # Assumes date is in format YYYY-MM-DD

    # Further filter to exclude "pending" bets
    df = df[df['status'] != 'pending']

    df['profit'] = df.apply(lambda x: x['odds'] - 1 if x['status'] == 'win' else -1 if x['status'] == 'loss' else 0, axis=1)
    
    wins = len(df[df['status'] == 'win'])
    losses = len(df[df['status'] == 'loss'])
    total_bets = len(df)
    settled_bets = wins + losses
    
    win_rate = (wins / settled_bets) * 100 if settled_bets > 0 else 0
    
    profit_emoji = "🚀" if df['profit'].sum() > 0 else "💔"
    
    summary_msg = (f"📊 *Monthly Summary for {current_month}*\n\n"
                   f"🎲 *Total Bets:* {total_bets}\n"
                   f"✅ *Wins:* {wins} ({win_rate:.2f}% win rate)\n"
                   f"❌ *Losses:* {losses}\n"
                   f"💹 *Average Odds:* {df['odds'].mean():.2f}\n"
                   f"{profit_emoji} *Profit:* {df['profit'].sum():.2f} units\n")
                   
    return summary_msg

async def main():
    await process_bets("pending")
    await process_bets("changed")
    
    if MESSAGES_SENT:
        print("Printing Daily Summary")
        await send_summary(mode="daily")
        
        print("Printing Monthly Summary")
        await send_summary(mode="monthly")

if __name__ == "__main__":
    asyncio.run(main())

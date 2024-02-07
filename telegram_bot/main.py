import os
import sys
import pandas as pd
from telegram import Bot
import asyncio
import logging
from datetime import datetime, timedelta
import pyshorteners

class DatabaseLoader:   
    def __init__(self, filename: str) -> None:
        self._filename = filename
        self._load_data()

    def _load_data(self) -> None:
        try:
            self._teams_data = pd.read_csv(self._filename)
        except FileNotFoundError:
            raise FileNotFoundError(f"The file {self._filename} does not exist")
        except pd.errors.EmptyDataError:
            raise ValueError(f"The file {self._filename} is empty")
        
        required_columns = {'t1', 't2', 'total_towers', 'total_dragons', 'total_barons', 'total_kills', 'league', 'year'}
        if not required_columns.issubset(self._teams_data.columns):
            missing_columns = required_columns - set(self._teams_data.columns)
            raise ValueError(f"The CSV file does not have the expected columns. Missing columns: {', '.join(missing_columns)}")

    def get_data(self) -> pd.DataFrame:
        return self._teams_data
    

data_loader = DatabaseLoader('database\data_transformed.csv')

TOKEN = '6475025056:AAE1jWC2aHVMpZVBAyAjFumimwnyTG2iuQo'
CHAT_ID = -1001891859269

# Get the directory of the script
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CSV_FILE_PATH = os.path.join(BASE_DIR, '..', 'bets', 'bets.csv')
BET_TRACK_PATH = os.path.join(BASE_DIR, 'bet_track.csv')


# Global flag to check if messages were sent
MESSAGE_DELAY = 1 
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
        # Introduce delay to prevent flooding
        await asyncio.sleep(MESSAGE_DELAY)
    except Exception as e:
        print(f"Error sending message: {e}")


async def process_bets(mode):
    df_bets = safe_read_csv(CSV_FILE_PATH)
    df_track = safe_read_csv(BET_TRACK_PATH)

    if mode == "pending":
        # Filter for pending bets
        pending_bets = df_bets[df_bets['status'] == 'pending']        
        # Group bets by game (date, league, team1, team2)
        # ADDED HOUSE
        grouped_bets = pending_bets.groupby(['date', 'league', 't1', 't2', 'House'])
        for _, bets_group in grouped_bets:
            # Check if the first bet in the group has been sent already by using filter_bets
            if not filter_bets(df_track, bets_group.iloc[0]).empty and \
               filter_bets(df_track, bets_group.iloc[0])['message_sent'].iloc[0] == 1:
                continue 
            # Initialize a list for messages for the current group (game)
            game_messages = []
            game_url = ""
            betting_house = ""
            for _, bet in bets_group.iterrows():
                    # Format message for each bet
                    message = format_csv_data_to_message(bet)
                    game_messages.append(message)
                    game_url = bet['url'] 
                    betting_house = bet['House'] # Assuming all bets in a group share the same URL
                    # Update the bet status in the log
                    update_or_log_bet_status(bet.to_dict())
                
            # Combine all bets for the same game into a single message
            if len(bets_group) > 1:
                message = reformat_game_messages(game_messages, game_url, betting_house)
                await send_message(message, bets_group.iloc[0].to_dict())  
            else:
                message = format_csv_data_to_message(bet)
                await send_message(message, bets_group.iloc[0].to_dict())  

    elif mode == "changed":
        status = "changed"
        changed_bets = pd.merge(df_bets, df_track, on=['date', 'league', 't1', 't2', 'bet_type', 'bet_line', 'House'], suffixes=('', '_tracked'))
        changed_bets = changed_bets[changed_bets['status'] != changed_bets['status_tracked']]
        # Group the changed bets by game
        # ADDED HOUSE
        grouped_changed_bets = changed_bets.groupby(['date', 'league', 't1', 't2', 'House'])

        for _, bets_group in grouped_changed_bets:
            game_messages = []
            game_url = ""
            betting_house = ""

            for _, bet in bets_group.iterrows():
                if bet['settled'] == 1:
                    continue  # Skip already settled bets

                message = format_csv_data_to_message(bet, bet['status'])
                game_messages.append(message)
                game_url = bet['url']
                betting_house = bet['House']

            # If there are messages to send for the group, format and send them
            if game_messages:
                combined_message = reformat_game_messages(game_messages, game_url, betting_house, status=status)
                await send_message(combined_message, bets_group.iloc[0].to_dict())

            # Update the bet status in the tracking log for all bets in the group
            for _, bet in bets_group.iterrows():
                update_or_log_bet_status(bet.to_dict(), "settle")

def get_team_game_count(team_name, database):
    team_games = database.query(f't1 == "{team_name}" or t2 == "{team_name}"')
    return len(team_games)

def reformat_game_messages(game_messages, game_url, betting_house, status=None):
    if status == "changed":
        combined_message = ""
        for msg in game_messages:
            combined_message += f"\n\n{msg}"
    else:
        header = game_messages[0].split('\n\n')[0]
        # Now build the combined message starting with the header
        combined_message = f"{header}\n🏠 {betting_house}"
        for msg in game_messages:
            # Extract the bet detail without the header and URL
            bet_detail = msg.split('\n\n')[1].rsplit('\n', 2)[0]  # Exclude the last line containing the old URL
            combined_message += f"\n\n{bet_detail}"
        shortened_url = shorten_url(game_url)    
        combined_message += f"\n{shortened_url}"

    return combined_message
    
def format_csv_data_to_message(row, status="pending"):
    # Fetch game counts for both teams
    team_a_game_count = get_team_game_count(row['t1'], data_loader.get_data())
    team_b_game_count = get_team_game_count(row['t2'], data_loader.get_data())
    
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

    roi_text = row['ROI']
    # Extract the numeric value from the ROI string
    roi_value = float(roi_text.strip('%'))
    if roi_value >= 30:
        roi_text += " 🚨"
    elif roi_value > 20:
        roi_text += " ⚠️"

    message = (f"{prefix} {emoji}\n"
            f"📅 Date: {row['date']}\n"
            f"🏆 League: {row['league']}\n"
            f"🥇 Match: {row['t1']} ({team_a_game_count} games) vs {row['t2']} ({team_b_game_count} games)\n"
            #f"🥇 Match: {row['t1']} vs {row['t2']}\n"
            f"\n🎲 TIP: {row['bet_type']} - {row['bet_line']}\n"
            f"📊 ROI: {roi_text}\n"
            # Place 'Fair Odds' and 'Odds' in the same line
            f"🔢 Odds: {row['odds']} | Fair Odds: {row['fair_odds']}\n"
            f"🏠 {row['House']}\n"
            f"🔗 {shortened_url}")
    return message


def get_summary(df, summary_type="daily"):
    df = safe_read_csv(CSV_FILE_PATH)
    current_date = datetime.now()
    
    if summary_type == "daily":
        date_filter = current_date.strftime('%Y-%m-%d')
    elif summary_type == "yesterday":
        date_filter = (current_date - timedelta(days=1)).strftime('%Y-%m-%d')
    elif summary_type == "monthly":
        month_number, year = datetime.now().month, datetime.now().year
        df = df[df['date'].str.startswith(f"{year}-{month_number:02}")]
        monthly_df = df[df['status'] != 'pending']
    else:
        raise ValueError("Invalid summary type. Choose 'daily', 'yesterday', or 'monthly'.")

    # Filter the dataframe
    if summary_type in ["daily", "yesterday"]:
        df = df[df['date'] == date_filter]

    # Common operations for all summaries
    wins = len(df[df['status'] == 'win'])
    losses = len(df[df['status'] == 'loss'])
    if not df.empty:
        df['profit'] = df.apply(lambda x: x['odds'] - 1 if x['status'] == 'win' else -1 if x['status'] == 'loss' else 0, axis=1)
    else:
        df['profit'] = 0
    profit = df['profit'].sum()


    # Formatting the summary message
    if summary_type == "monthly":
        total_bets = len(monthly_df)
        settled_bets = wins + losses
        win_rate = (wins / settled_bets) * 100 if settled_bets > 0 else 0
        average_odds = df['odds'].mean() if len(monthly_df) > 0 else 0
        profit_emoji = "🚀" if profit > 0 else "💔"
        summary = (f"📊 *Monthly Summary for {current_date.strftime('%B - %Y')}*\n"
                   f"🎲 *Total Bets:* {total_bets}\n"
                   f"✅ *Wins:* {wins} ({win_rate:.2f}% win rate)\n"
                   f"❌ *Losses:* {losses}\n"
                   f"💹 *Average Odds:* {average_odds:.2f}\n"
                   f"{profit_emoji} *Profit:* {profit:.2f} units\n")
    else:
        date_label = "Daily" if summary_type == "daily" else "Yesterday's"
        summary = (f"📊 *{date_label} Summary for {date_filter}:*\n"
                   f"✅ *Wins:* {wins} | ❌ *Losses:* {losses}\n"
                   f"💰 *Profit:* {profit:.2f} units")
    return summary

async def send_summary():
    df = safe_read_csv(CSV_FILE_PATH)
    # Retrieve all the summaries.
    daily_summary_msg = get_summary(df, "daily")
    yesterdays_summary_msg = get_summary(df, "yesterday")
    monthly_summary_msg = get_summary(df, "monthly")
    # Combine all summaries into one message.
    combined_summary = (f"{daily_summary_msg}\n\n"
                        f"{yesterdays_summary_msg}\n\n"
                        f"{monthly_summary_msg}")
    
    # Initialize the bot with the token and send the combined message.
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=combined_summary, parse_mode='Markdown')

async def main():
    # df_bets = pd.read_csv(CSV_FILE_PATH)
    # bet_to_send = df_bets.iloc[379]
    # message = format_csv_data_to_message(bet_to_send)
    # await send_message(message, bet_to_send.to_dict())
    try:
        await process_bets("pending")
        await process_bets("changed")

        if MESSAGES_SENT:
            print("Printing Combined Summary")
            await send_summary()
    except Exception as e:
        print(f"An error occurred: {e}")
    

if __name__ == "__main__":
    asyncio.run(main())

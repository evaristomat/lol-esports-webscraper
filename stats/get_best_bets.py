import os
import pandas as pd
import csv
import json
import logging
import glob
from odds_comparator import OddsComparator
from datetime import datetime
from colorama import init, Fore
from datetime import datetime, timedelta

init(autoreset=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def row_identifier(row):
    return f"{row['date']}-{row['t1']}-{row['t2']}-{row['bet_type']}-{row['bet_line']}-{row['House']}"

def build_row(best_bet, bet_line_key):
    """Build row dictionary from the best_bet dictionary."""
    bet_line = f"{bet_line_key} {best_bet.get(bet_line_key, '')}"
    return {
        'date': best_bet.get('date', ''),
        'league': best_bet.get('league', ''),
        't1': best_bet.get('t1', ''),
        't2': best_bet.get('t2', ''),
        'bet_type': best_bet.get('bet', ''),
        'bet_line': bet_line,
        'ROI': best_bet.get('ROI', ''),
        "fair_odds": best_bet.get('fair_odds', ''),
        'odds': best_bet.get('odds', ''),
        'url': best_bet.get('url', ''),
        'status': 'pending'
    }

def remove_old_pending_bets(csv_path, days_threshold=3):
    """
    Remove bets from the CSV file that are more than 'days_threshold' days old
    with 'pending' status.
    """
    # Check if the CSV file exists
    if not os.path.exists(csv_path):
        return  # If the CSV doesn't exist, there's nothing to clean.
    
    # Read the CSV file into a DataFrame
    bets_df = pd.read_csv(csv_path, parse_dates=['date'])
    
    # Get the current date
    today = datetime.today().date()

    # Filter out rows where the 'status' is 'pending' and the 'date' is older than the threshold
    is_recent_or_not_pending = (today - bets_df['date'].dt.date) <= timedelta(days=days_threshold)
    is_not_pending_status = bets_df['status'] != 'pending'
    filtered_df = bets_df[is_recent_or_not_pending | is_not_pending_status]
    
    # Write the filtered DataFrame back to the CSV
    filtered_df.to_csv(csv_path, index=False)

def main():
# Absolute paths
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    data_folder = os.path.join(project_root, 'data')
    processed_files_log = os.path.join(project_root, 'logs/best_bets.log')
    filename = os.path.join(project_root, 'database', 'data_transformed.csv')

    header = ['date', 'league', 't1', 't2', 'bet_type', 'bet_line', 'ROI','fair_odds', 'odds', 'House', 'url', 'status']

    processed_files = set()
    if os.path.exists(processed_files_log):
        with open(processed_files_log, 'r') as log_file:
            processed_files = set(log_file.read().splitlines())

    csv_folder = os.path.join(project_root, 'bets')
    csv_filename = 'bets.csv'
    csv_path = os.path.join(csv_folder, csv_filename)

    os.makedirs(csv_folder, exist_ok=True)
    existing_rows = set()

    # Exception handling for CSV reading
    try:
        if os.path.exists(csv_path):
            with open(csv_path, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                rows = sorted(reader, key=lambda x: (datetime.strptime(x['date'], '%Y-%m-%d'), x['t1']))
                for row in rows:
                    existing_rows.add(row_identifier(row))
    except Exception as e:
        logging.error(f"Error reading CSV file {csv_path}: {e}")
        return  # Exit the script if there's an error reading the CSV
    
    # Before adding new rows, clean up old 'pending' rows
    remove_old_pending_bets(csv_path)

    all_new_rows = []

    # Error handling for each JSON file
    for year_folder in os.listdir(data_folder):
        year_path = os.path.join(data_folder, year_folder)
        if not os.path.isdir(year_path):
            continue
        logging.info(f'Entering year directory: {year_folder}')
        for month_folder in os.listdir(year_path):
            month_path = os.path.join(year_path, month_folder)
            if not os.path.isdir(month_path):
                continue
            logging.info(f'Entering month directory: {month_folder}')
            for date_folder in os.listdir(month_path):
                date_path = os.path.join(month_path, date_folder)
                if not os.path.isdir(date_path):
                    continue
                logging.info(Fore.YELLOW + f'Entering date directory: {date_folder}' + Fore.RESET)
                json_files = glob.glob(os.path.join(date_path, 'games_*.json'))
                for json_file_path in json_files:
                    if json_file_path in processed_files:
                        logging.info(f"Skipping already processed file: {json_file_path}")
                        continue
                    try:
                        with open(json_file_path, 'r') as file:
                            games = json.load(file)
                    except (FileNotFoundError, json.JSONDecodeError) as e:
                        logging.error(f"Error reading {json_file_path}: {e}")
                        continue

                    house_name = os.path.basename(json_file_path).split('_')[1].replace('Webscraper.json', '')
                    logging.info(f"House name: {house_name}")

                    for game_data in games:
                        teamA = game_data['overview'].get('home_team', 'Unknown Team')  # Safely retrieve home team's name
                        teamB = game_data['overview'].get('away_team', 'Unknown Team')  # Safely retrieve away team's name
                        logging.info(Fore.YELLOW + f"Checking bets for match - {teamA} vs {teamB}")  # Log the match being checked in yellow
                        
                        comparator = OddsComparator(filename, game_data)
                        best_dragon = comparator.compare_dragon()
                        best_tower = comparator.compare_tower()
                        best_kills = comparator.compare_kills()
                        best_fd = comparator.compare_first_drake()
                        bets_gameduration = comparator.compare_game_duration()
                        best_total_inhibitor = comparator.compare_total_inhibitor()
                        best_total_barons = comparator.compare_total_barons()

                        for bet, bet_line_key in [(best_dragon, 'total_dragons'),
                                                (best_tower, 'total_towers'),
                                                (best_kills, 'total_kills'),
                                                (best_fd, 'first_dragon'),
                                                (bets_gameduration, 'game_duration'),
                                                (best_total_inhibitor, 'total_inhibitors'),
                                                (best_total_barons, 'total_barons')]:
                            if bet:
                                row = build_row(bet, bet_line_key)
                                print(row)
                                row['House'] = house_name
                                identifier = row_identifier(row)

                                # Check for ROI >= 5%
                                try:
                                    roi_value = float(row['ROI'].replace('%', '').strip())  # Remove % sign and convert to float
                                    if roi_value < 5.0:  # If ROI is less than 3%, skip this row
                                        logging.info(f"Skipping bet with ROI {roi_value}% which is less than 5%.")
                                        continue
                                except ValueError:  # Handle cases where 'ROI' can't be converted to a float
                                    logging.warning(f"Invalid ROI value: {row['ROI']}. Skipping bet.")
                                    continue

                                if identifier not in existing_rows:
                                    all_new_rows.append(row)  # Collect new rows for sorting
                                    existing_rows.add(identifier)  # Adding the identifier of the new row to the set
                                else:
                                    logging.info(f"Row already exists: {row}")
                            else:
                                logging.info(f"No best bet found for {bet_line_key}")

                    with open(processed_files_log, 'a') as log_file:
                        log_file.write(json_file_path + '\n')

    # Writing to CSV, with error handling
    try:
        with open(csv_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=header, quoting=csv.QUOTE_MINIMAL)
            if file.tell() == 0:
                writer.writeheader()
            for row in all_new_rows:
                writer.writerow(row)
    except Exception as e:
        logging.error(f"Error writing to CSV {csv_path}: {e}")


if __name__ == "__main__":
    main()

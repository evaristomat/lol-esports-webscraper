import os
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from odds_comparator import OddsComparator
from colorama import init, Fore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
init(autoreset=True)

# Global variable for ROI threshold
ROI_THRESHOLD = 5.0  # 5%

def build_row(best_bet, bet_line_key):
    """Build row DataFrame from the best_bet dictionary."""
    bet_line = f"{bet_line_key} {best_bet.get(bet_line_key, '')}"
    row = pd.DataFrame({
        'date': [best_bet.get('date', '')],
        'league': [best_bet.get('league', '')],
        't1': [best_bet.get('t1', '')],
        't2': [best_bet.get('t2', '')],
        'bet_type': [best_bet.get('bet', '')],
        'bet_line': [bet_line],
        'ROI': [best_bet.get('ROI', '')],
        'fair_odds': [best_bet.get('fair_odds', '')],
        'odds': [best_bet.get('odds', '')],
        'url': [best_bet.get('url', '')],
        'status': ['pending']
    })
    return row

def row_identifier(row):
    # Define a unique identifier based on the information you have in a row
    # For example, combining date, teams, and bet_type could be unique
    return f"{row['date']}-{row['t1']}-{row['t2']}-{row['bet_type']}-{row['bet_line']}-{row['House']}"

def remove_old_pending_bets(csv_path, days_threshold=3):
    if csv_path.is_file():
        bets_df = pd.read_csv(csv_path, parse_dates=['date'])
        today = pd.to_datetime('today').normalize()
        threshold_date = today - timedelta(days=days_threshold)
        
        # Filter out rows where 'status' is 'pending' and 'date' is older than the threshold
        is_recent_or_not_pending = (bets_df['date'] >= threshold_date) | (bets_df['status'] != 'pending')
        filtered_df = bets_df[is_recent_or_not_pending]
        
        filtered_df.to_csv(csv_path, index=False)

def is_teamname_in_database(team_name, teams_data) -> bool:
    """Check if the team name exists in the database."""
    return any(teams_data['t1'].eq(team_name) | teams_data['t2'].eq(team_name))

def process_json_files(data_folder, processed_files_log, csv_path, filename, teams_data):
    project_root = Path(__file__).parent.parent
    data_folder = project_root / 'data'
    processed_files = pd.read_csv(processed_files_log, header=None, names=['file']).squeeze('columns').tolist() if processed_files_log.is_file() else []
    all_new_rows = []

    # Load existing data if `bets.csv` exists
    if csv_path.is_file():
        existing_bets_df = pd.read_csv(csv_path)
        # Create a set of identifiers from existing rows for quick lookup
        existing_identifiers = set(existing_bets_df.apply(row_identifier, axis=1))
    else:
        existing_identifiers = set()
    
    for json_file_path in data_folder.glob('**/games_*.json'):
        if str(json_file_path) in processed_files:
            relative_path = os.path.relpath(json_file_path, start=os.path.commonpath([json_file_path, os.getcwd()]))
            logging.info(f"Skipping already processed file: {relative_path}")
            continue

        house_name = os.path.basename(json_file_path).split('_')[1].replace('Webscraper.json', '')
        try:
            with open(json_file_path, 'r') as file:
                games = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error reading {json_file_path}: {e}")
            continue

        for game_data in games:
            teamA = game_data['overview'].get('home_team', 'Unknown Team')
            teamB = game_data['overview'].get('away_team', 'Unknown Team')
            logging.info(Fore.YELLOW + f"Checking bets for match - {teamA} vs {teamB}" + Fore.RESET)

            comparator = OddsComparator(filename, game_data)

            # Assuming teams_data is your dataframe containing teams' information
            if not is_teamname_in_database(teamA, teams_data) or not is_teamname_in_database(teamB, teams_data):
                #logging.info(Fore.RED + f"One or both of the teams: {teamA}, {teamB} are not in the database. Skipping to next game."  + Fore.RESET)
                continue
            
            try:
                best_bets = [
                    comparator.compare_dragon(),
                    comparator.compare_tower(),
                    comparator.compare_kills(),
                    comparator.compare_first_drake(),
                    comparator.compare_game_duration(),
                    comparator.compare_total_inhibitor(),
                    comparator.compare_total_barons()
                ]

                bet_line_keys = [
                    'total_dragons',
                    'total_towers',
                    'total_kills',
                    'first_dragon',
                    'game_duration',
                    'total_inhibitors',
                    'total_barons'
                ]
                
                for bet, bet_line_key in zip(best_bets, bet_line_keys):
                    if bet:
                        row = build_row(bet, bet_line_key)
                        row['House'] = house_name

                        # Ensure the row columns match the CSV file's columns
                        correct_order = ['date', 'league', 't1', 't2', 'bet_type', 'bet_line', 'ROI', 'fair_odds', 'odds', 'House', 'url', 'status']
                        row = row[correct_order]
                        
                        # Calculate identifier for the new row
                        identifier = row_identifier(row.iloc[0])
                        #print(identifier)
                        try:
                            roi_value = float(row['ROI'].iloc[0].replace('%', '').strip())
                            if roi_value < ROI_THRESHOLD:
                                logging.info(f"Skipping bet with ROI {roi_value}% which is less than {ROI_THRESHOLD}%.")
                                continue
                        except ValueError:
                            logging.warning(f"Invalid ROI value: {row['ROI']}. Skipping bet.")
                            continue
                                
                        if identifier not in existing_identifiers:
                            logging.info(Fore.GREEN + f"Best bet found for {bet_line_key}" + Fore.RESET)
                            all_new_rows.append(row)
                            existing_identifiers.add(identifier)
                        else:
                            logging.info(Fore.MAGENTA + f"Row already exists for {row['bet_line'][0]}" + Fore.RESET)
                    else:
                        logging.info(f"No best bet found for {bet_line_key}")
            except:
                continue            
        # Append to processed files log
        with open(processed_files_log, 'a') as log_file:
            log_file.write(str(json_file_path) + '\n')

    # Append new rows to the CSV
    if all_new_rows:
        pd.concat(all_new_rows).to_csv(csv_path, mode='a', header=not csv_path.is_file(), index=False)

# Inside main, you would pass `filename` to `process_json_files`:
def main():
    project_root = Path(__file__).parent.parent
    processed_files_log = project_root / 'logs/best_bets.log'
    csv_path = project_root / 'bets' / 'bets.csv'
    filename = project_root / 'database' / 'data_transformed.csv'

    # Ensure CSV folder exists
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Load teams data
    teams_data = pd.read_csv(filename)

    # Before adding new rows, clean up old 'pending' rows
    remove_old_pending_bets(csv_path)

    # Process JSON files and update CSV
    process_json_files(project_root / 'data', processed_files_log, csv_path, filename, teams_data)

if __name__ == "__main__":
    main()
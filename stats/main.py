import os
import csv
import json
import logging
import glob
from odds_comparator import OddsComparator  # Replace with your actual import

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def row_exists(rows, row):
    """Check if the row already exists in the existing rows."""
    return any(all(row[field] == existing_row[field] for field in row) for existing_row in rows)

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
        'odds': best_bet.get('odds', ''),
        'status': 'pending'
    }


def main():
    filename = '../database/data_transformed.csv'
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    data_folder = os.path.join(project_root, 'data')
    processed_files_log = os.path.join(project_root, 'processed_files.log')

    header = ['date', 'league', 't1', 't2', 'bet_type', 'bet_line', 'ROI', 'odds', 'House', 'status']

    processed_files = set()
    if os.path.exists(processed_files_log):
        with open(processed_files_log, 'r') as log_file:
            processed_files = set(log_file.read().splitlines())

    csv_folder = os.path.join(project_root, 'bets')
    csv_filename = 'bets.csv'
    csv_path = os.path.join(csv_folder, csv_filename)

    os.makedirs(csv_folder, exist_ok=True)
    existing_rows = set()  # Using a set to store unique identifiers of the existing rows

    if os.path.exists(csv_path):
        with open(csv_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                existing_rows.add(row_identifier(row))

    for date_folder in os.listdir(data_folder):
        json_files = glob.glob(os.path.join(data_folder, date_folder, 'games_*.json'))

        for json_file_path in json_files:
            if json_file_path in processed_files:
                #logging.info(f"Skipping already processed file: {json_file_path}")
                logging.info(f"Skipping already processed file")
                continue

            try:
                with open(json_file_path, 'r') as file:
                    games = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logging.error(f"Error reading {json_file_path}: {e}")
                continue

            house_name = os.path.basename(json_file_path).split('_')[1].replace('Webscraper.json', '')

            with open(csv_path, mode='a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=header)
                if file.tell() == 0:
                    writer.writeheader()

                for game_data in games:
                    comparator = OddsComparator(filename, game_data)
                    best_dragon = comparator.compare_dragon()
                    best_tower = comparator.compare_tower()

                    for bet, bet_line_key in [(best_dragon, 'total_dragons'), (best_tower, 'total_towers')]:
                        if bet:
                            row = build_row(bet, bet_line_key)
                            row['House'] = house_name
                            identifier = row_identifier(row)

                            if identifier not in existing_rows:
                                writer.writerow(row)
                                existing_rows.add(identifier)  # Adding the identifier of the new row to the set
                            else:
                                logging.info(f"Row already exists: {row}")
                        else:
                            logging.info(f"No best bet found for {bet_line_key}")

            with open(processed_files_log, 'a') as log_file:
                log_file.write(json_file_path + '\n')

if __name__ == "__main__":
    main()
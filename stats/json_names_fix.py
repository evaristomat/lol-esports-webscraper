import pandas as pd
from fuzzywuzzy import process
import json
import os
import glob
import logging
from colorama import init, Fore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
init(autoreset=True)

# Get the current script directory
current_script_directory = os.path.dirname(os.path.realpath(__file__))
# Go up two levels to get the root directory
root_directory = os.path.dirname(current_script_directory)

def read_db_names(csv_filepath):
    df = pd.read_csv(csv_filepath)
    team_names = pd.concat([df['t1'], df['t2']]).unique().tolist()
    return team_names

def correct_names_in_json(json_file_path, db_names, name_corrections):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        json_data = json.load(file)

    for game in json_data:
        for team_type in ['home_team', 'away_team']:
            team_name = game['overview'][team_type]
            team_name_clean = team_name.replace(" (Kills)", "")
            team_name_corrected = name_corrections.get(team_name_clean, team_name_clean)

            if team_name_corrected != team_name_clean:  # Log if a correction from the dictionary was applied
                logging.info(Fore.YELLOW + f"Dictionary corrected {team_type} name: '{team_name_clean}' to '{team_name_corrected}'" + Fore.RESET)

            if team_name_corrected not in db_names:
                closest_match = process.extractOne(team_name_corrected, db_names, score_cutoff=90)
                if closest_match:
                    logging.info(Fore.YELLOW + f"Fuzzy matched {team_type} name: '{team_name_corrected}' to '{closest_match[0]}'" + Fore.RESET)
                    team_name_corrected = closest_match[0]

            game['overview'][team_type] = team_name_corrected

    with open(json_file_path, 'w', encoding='utf-8') as file:
        json.dump(json_data, file, indent=4)


    # Write the corrected data back to the file
    with open(json_file_path, 'w', encoding='utf-8') as file:
        json.dump(json_data, file, indent=4)



# Function to log processed files
def log_processed_file(log_file_path, file_path):
    with open(log_file_path, 'a') as log_file:
        log_file.write(file_path + '\n')

# Function to check if the file was processed
def is_file_processed(log_file_path, file_path):
    if not os.path.isfile(log_file_path):
        return False
    with open(log_file_path, 'r') as log_file:
        processed_files = log_file.read().splitlines()
    return file_path in processed_files

# Function to process JSON files in a directory
def process_json_files_in_directory(db_names, directory_path, log_file_path, name_corrections):
    for file_path in glob.glob(os.path.join(directory_path, '*.json')):
        if not is_file_processed(log_file_path, file_path):
            # Pass name_corrections to correct_names_in_json
            correct_names_in_json(file_path, db_names, name_corrections)
            log_processed_file(log_file_path, file_path)

def process_all_json_files(db_names, name_corrections):
    logs_directory = os.path.join(root_directory, 'logs')
    data_directory = os.path.join(root_directory, 'data')

    log_file_path = os.path.join(logs_directory, 'name_fix.log')
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)

    for year in os.listdir(data_directory):
        year_path = os.path.join(data_directory, year)
        if not os.path.isdir(year_path):
            continue
        for month in os.listdir(year_path):
            month_path = os.path.join(year_path, month)
            if not os.path.isdir(month_path):
                continue
            for day in os.listdir(month_path):
                day_path = os.path.join(month_path, day)
                if not os.path.isdir(day_path):
                    continue
                # Pass name_corrections to process_json_files_in_directory
                process_json_files_in_directory(db_names, day_path, log_file_path, name_corrections)

name_corrections = {
    "Karmine Corp.A": "Karmine Corp Blue",
    "Team BDS.A": "Team BDS Academy",
    "Orbit Anonymo": "Orbit Anonymo Esports",
    "Kwangdong Freecs.Ch": "Kwangdong Freecs Challengers",
    "DRX.Ch": "DRX Challengers",
    "FearX.Y": "FearX Youth",
    "Hanwha Life Esports.Ch":"Hanwha Life Esports Challengers",
    "Gen.G.GA":"Gen.G Global Academy",
    "T1.EA":"T1 Esports Academy",
    "KT Rolster.Ch":"KT Rolster Challengers",
    "OKSavingsBank BRION.Ch":"OKSavingsBank BRION Challengers",
    "Dplus KIA.Ch":"Dplus KIA Challengers",
    "Nongshim.EA":"",
    "Besiktas Esports":"Beşiktaş Esports",
    "BKROG": "BK ROG Esports",
    "UCAM Tokiers": "UCAM Esports",
    "big":"Berlin International Gaming",
    "AF willhaben":"Austrian Force willhaben"
}

# Main execution
if __name__ == "__main__":
    # Path to the CSV file relative to the script
    db_names_filepath = os.path.join(root_directory, 'database', 'data_transformed.csv')
    # Read the database names
    db_names = read_db_names(db_names_filepath)
    # Process Pinnacle JSON files with name corrections
    process_all_json_files(db_names, name_corrections)
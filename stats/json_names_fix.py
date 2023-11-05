import pandas as pd
from fuzzywuzzy import process
import json
import os

# Get the current script directory
current_script_directory = os.path.dirname(os.path.realpath(__file__))
# Go up two levels to get the root directory
root_directory = os.path.dirname(current_script_directory)

def read_db_names(csv_filepath):
    df = pd.read_csv(csv_filepath)
    team_names = pd.concat([df['t1'], df['t2']]).unique().tolist()
    return team_names

def correct_names_in_json(json_file_path, db_names):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        json_data = json.load(file)

    # Loop through each game and update the names
    for game in json_data:
        home_team = game['overview']['home_team']
        away_team = game['overview']['away_team']
        
        home_team_clean = home_team.replace(" (Kills)", "")
        away_team_clean = away_team.replace(" (Kills)", "")

        closest_home = process.extractOne(home_team_clean, db_names, score_cutoff=80)
        closest_away = process.extractOne(away_team_clean, db_names, score_cutoff=80)
        
        if closest_home:
            game['overview']['home_team'] = closest_home[0]
        if closest_away:
            game['overview']['away_team'] = closest_away[0]

    # Write the updated data back to the JSON file
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

# Main script to process files
def process_pinnacle_json_files(root_directory, db_names):
    logs_directory = os.path.join(root_directory, 'logs')
    log_file_path = os.path.join(logs_directory, 'name_fix.log')
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)

    for year in os.listdir(root_directory):
        year_path = os.path.join(root_directory, year)
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
                for file_name in os.listdir(day_path):
                    # Check if the file is a Pinnacle JSON
                    if "games_PinnacleWebscraper.json" in file_name:
                        file_path = os.path.join(day_path, file_name)
                        # Check if the file has been processed
                        if not is_file_processed(log_file_path, file_path):
                            # Process the JSON file
                            correct_names_in_json(file_path, db_names)
                            # Log the processed file
                            log_processed_file(log_file_path, file_path)

def process_pinnacle_json_files(db_names):
    logs_directory = os.path.join(root_directory, 'logs')
    data_directory = os.path.join(root_directory, 'data')

    log_file_path = os.path.join(logs_directory, 'name_fix.log')
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)

    # Assuming the year, month, and day are dynamically found
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
                for file_name in os.listdir(day_path):
                    if "games_PinnacleWebscraper.json" in file_name:
                        file_path = os.path.join(day_path, file_name)
                        if not is_file_processed(log_file_path, file_path):
                            correct_names_in_json(file_path, db_names)
                            log_processed_file(log_file_path, file_path)

# Main execution
if __name__ == "__main__":
    # Path to the CSV file relative to the script
    db_names_filepath = os.path.join(root_directory, 'database', 'data_transformed.csv')
    # Read the database names
    db_names = read_db_names(db_names_filepath)
    # Process Pinnacle JSON files
    process_pinnacle_json_files(db_names)
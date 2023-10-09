import json
import os
import logging

# Setup logging
LOG_FILENAME = 'logs/update_dafa_json.log'
PROCESSED_FOLDERS_LOG = 'logs/processed_folders.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def folder_already_processed(folder_name):
    """Check if a folder has been processed before."""
    with open(PROCESSED_FOLDERS_LOG, 'a+') as f:  # 'a+' mode to read and append
        f.seek(0)  # Move to the beginning of the file before reading
        processed_folders = f.readlines()
        return folder_name + '\n' in processed_folders  # Check if folder is in the list

def mark_folder_as_processed(folder_name):
    """Mark a folder as processed."""
    with open(PROCESSED_FOLDERS_LOG, 'a') as f:
        f.write(folder_name + '\n')

# Define the function to replace the key in a JSON file
def replace_key_in_file(file_path):
    # Load the data from the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Iterate over the data to find and replace the key
    for entry in data:
        if "total_dragons" in entry:
            entry["first_dragon"] = entry.pop("total_dragons")

    # Save the modified data back to the JSON file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

    logging.info(f"Replaced 'total_dragons' with 'first_dragon' in {file_path}")

# Path to your main folder
main_folder_path = 'data'

# Traverse through each subfolder
for folder_name in os.listdir(main_folder_path):
    if folder_already_processed(folder_name):
        logging.info(f"Skipping folder {folder_name} as it was already processed.")
        continue  # Skip to next folder

    folder_path = os.path.join(main_folder_path, folder_name)
    if os.path.isdir(folder_path):
        target_file = os.path.join(folder_path, 'games_DafabetWebscraper.json')
        if os.path.exists(target_file):  # Check if the specific file exists
            try:
                replace_key_in_file(target_file)
                mark_folder_as_processed(folder_name)  # Mark the folder as processed after the file is updated
            except Exception as e:
                logging.error(f"Error updating {target_file}. Error message: {str(e)}")

logging.info("JSON updates completed.")
import os
import gdown
import logging
from logging.handlers import RotatingFileHandler
from colorama import init, Fore

# Initialize colorama
init(autoreset=True)

# Setup the path for logging
log_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_directory, exist_ok=True)  # Ensure the logs directory exists
log_path = os.path.join(log_directory, 'data_processing.log')

# Configure logging with rotation
logging.basicConfig(handlers=[RotatingFileHandler(filename=log_path, 
                                                  maxBytes=5*1024*1024, 
                                                  backupCount=5)],
                    level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def log(message, level='info'):
    """Prints a message in yellow with brackets and logs it."""
    print(f"{Fore.YELLOW}[{message}]{Fore.RESET}")
    if level == 'info':
        logging.info(message)
    elif level == 'error':
        logging.error(message)

def download_from_gdrive(url, folder, filename):
    file_id = url.split('/')[-2]
    direct_url = f'https://drive.google.com/uc?id={file_id}'
    csv_path = os.path.join(folder, f"{filename}.csv")
    backup_csv_path = os.path.join(folder, f"{filename}_backup.csv")

    # Check if a backup exists, if not, rename current CSV to backup
    if not os.path.exists(backup_csv_path) and os.path.exists(csv_path):
        log(f"Found existing csv file. Renaming to backup...")
        try:
            os.rename(csv_path, backup_csv_path)
            log("Existing file renamed successfully.")
        except Exception as e:
            log(f"Error renaming file: {e}", 'error')
            return False  # Stop the script if renaming fails

    # If a backup exists, delete current CSV
    if os.path.exists(csv_path):
        log(f"Deleting existing csv file...")
        try:
            os.remove(csv_path)
            log("Existing file deleted successfully.")
        except Exception as e:
            log(f"Error deleting file: {e}", 'error')
            return False  # Stop the script if deletion fails

    log(f"Downloading the file to {csv_path}...")
    gdown.download(direct_url, csv_path, quiet=False)
    
    # Check if the file was downloaded successfully
    if os.path.exists(csv_path):
        log("Updated successfully!")
        return True
    else:
        log("Download failed!", 'error')
        return False

if __name__ == "__main__":
    shared_url = "https://drive.google.com/file/d/1XXk2LO0CsNADBB1LRGOV5rUpyZdEZ8s2/view?usp=sharing"
    folder_path = os.path.dirname(os.path.abspath(__file__))
    filename = "database"

    if download_from_gdrive(shared_url, folder_path, filename):
        logging.info("Database Updated.")
    else:
        logging.error("Database Update Failed.")

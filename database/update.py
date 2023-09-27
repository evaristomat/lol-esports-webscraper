import os
import gdown
import logging

# Configure logging
logging.basicConfig(filename='data_processing.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

YELLOW = '\033[93m'
ENDC = '\033[0m'

def log(message):
    """Prints a message in yellow with brackets."""
    print(f"{YELLOW}[{message}]{ENDC}")

def download_from_gdrive(url, folder, filename):
    file_id = url.split('/')[-2]
    direct_url = f'https://drive.google.com/uc?id={file_id}'
    csv_path = os.path.join(folder, f"{filename}.csv")

    if os.path.exists(csv_path):
        log(f"Found existing csv file. Deleting...")
        try:
            os.remove(csv_path)
            log("Existing file deleted successfully.")
        except Exception as e:
            log(f"Error deleting file: {e}")

    log(f"Downloading the file to {csv_path}...")
    gdown.download(direct_url, csv_path, quiet=False)
    log(f"Updated successfully!")

if __name__ == "__main__":
    shared_url = "https://drive.google.com/file/d/1XXk2LO0CsNADBB1LRGOV5rUpyZdEZ8s2/view?usp=drive_link"
    folder_path = os.path.dirname(os.path.abspath(__file__))
    filename = "database"

    download_from_gdrive(shared_url, folder_path, filename)
    # Log completion
    logging.info("Database Uptaded.")

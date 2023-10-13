import pandas as pd
from tqdm import tqdm
import logging
import os

# Configure logging
logging.basicConfig(filename='data_processing.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get the directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))
bets_path = os.path.join(script_dir, 'database.csv')
data = pd.read_csv(bets_path)

YELLOW = '\033[93m'
ENDC = '\033[0m'
def log(message):
    """Prints a message in yellow with brackets."""
    print(f"{YELLOW}[{message}]{ENDC}")
    
def get_league_matchups_global(df, league_name=None):
    """
    Process the dataframe to generate league matchups based on participant IDs.

    Parameters:
    - df (pd.DataFrame): The input dataframe.
    - league_name (str, optional): If specified, filters the dataframe for the given league name.

    Returns:
    - pd.DataFrame: A dataframe with merged information for both participant IDs 100 and 200.
    """

    # Filter data by league name, if provided
    if league_name:
        df = df[df.league == league_name]

    # Filter data to retain rows with participant IDs 100 and 200
    league_compositions = df[df.participantid.isin([100, 200])].copy()

    # Build champion mapping and assign champions to respective roles
    champion_mapping = build_champion_dict(df)
    roles = ["top", "jung", "mid", "adc", "sup"]
    for idx, role in enumerate(roles):
        league_compositions[role] = league_compositions.apply(
            lambda row: get_champion_optimized(row, idx, champion_mapping), axis=1
        )

    # Split the compositions based on participant IDs and merge them
    league_100_compositions = league_compositions[league_compositions["participantid"] == 100]
    league_200_compositions = league_compositions[league_compositions["participantid"] == 200]
    merged_leagues = league_100_compositions.merge(league_200_compositions, how='left', on="gameid")

    renamed_columns = {
        "league_x": "league",
        "year_x": "year",
        "date_x": "date",
        "game_x": "game",
        "patch_x": "patch",
        "side_x": "side",
        "teamname_x": "t1",
        "teamname_y": "t2",
        "result_x": "result_t1",
        "gamelength_x": "gamelength",
        "top_x": "top_t1",
        "jung_x": "jung_t1",
        "mid_x": "mid_t1",
        "adc_x": "adc_t1",
        "sup_x": "sup_t1",
        "kills_x": "kills_t1",
        "firstdragon_x": "firstdragon_t1",
        "dragons_x": "dragons_t1",
        "barons_x": "barons_t1",
        "firstherald_x": "firstherald_t1",
        "firstbaron_x": "firstbaron_t1",
        "firsttower_x": "firsttower_t1",
        "towers_x": "towers_t1",
        "top_y": "top_t2",
        "jung_y": "jung_t2",
        "mid_y": "mid_t2",
        "adc_y": "adc_t2",
        "sup_y": "sup_t2",
        "kills_y": "kills_t2",
        "firstdragon_y": "firstdragon_t2",
        "dragons_y": "dragons_t2",
        "barons_y": "barons_t2",
        "firstherald_y": "firstherald_t2",
        "firstbaron_y": "firstbaron_t2",
        "firsttower_y": "firsttower_t2",
        "towers_y": "towers_t2",
        "inhibitors_x": "inhibitors_t1",
        "inhibitors_y": "inhibitors_t2"
    }

    # Filter and rename columns
    final_df = merged_leagues[list(renamed_columns.keys())]
    final_df = final_df.rename(columns=renamed_columns)

    # Convert date column to datetime format
    final_df.loc[:, 'date'] = pd.to_datetime(final_df['date'], format="%Y-%m-%d %H:%M:%S")
    final_df.loc[:, 'gamelength'] = (final_df['gamelength'] / 60).round(2)
    
    final_df['total_kills'] = final_df['kills_t1'] + final_df['kills_t2']
    final_df['total_barons'] = final_df['barons_t1'] + final_df['barons_t2']
    final_df['total_towers'] = final_df['towers_t1'] + final_df['towers_t2']
    final_df['total_dragons'] = final_df['dragons_t1'] + final_df['dragons_t2']
    final_df['total_inhibitors'] = final_df['inhibitors_t1'] + final_df['inhibitors_t2']


    return final_df

def build_champion_dict(df):
    """
    Build a dictionary mapping (gameid, participantid) to champion.

    Parameters:
    - df (pd.DataFrame): Dataframe with columns 'gameid', 'participantid', and 'champion'.

    Returns:
    - dict: A dictionary with (gameid, participantid) as keys and champion as value.
    """

    # Create a dictionary using a comprehension
    champion_dict = {(game_id, participant_id): champion_name 
                     for game_id, participant_id, champion_name 
                     in zip(df["gameid"], df["participantid"], df["champion"])}

    return champion_dict



def get_champion_optimized(row, role, champion_dict):
    """
    Retrieve the champion based on role and participant ID.

    Parameters:
    - row (pd.Series): A row from the dataframe.
    - role (int): An integer representing the role (0 for top, 1 for jungle, etc.).
    - champion_dict (dict): A dictionary with game and participant ID as keys and champion as value.

    Returns:
    - str: The champion name.
    """

    # Determine the starting participant ID based on the team
    base_participant_id = 1 if row["participantid"] == 100 else 6

    # Calculate the specific participant ID for the role
    specific_participant_id = base_participant_id + role

    # Fetch the champion using the game ID and the specific participant ID
    champion = champion_dict.get((row["gameid"], specific_participant_id))

    return champion

if __name__ == "__main__":
    # Initialize the progress bar
    total_rows = len(data)
    log(f"Data_transformation.py initiated")
    with tqdm(total=total_rows, desc="Processing") as pbar:
        datatest = get_league_matchups_global(data)
        data_transformed_path = os.path.join(script_dir, 'data_transformed.csv')  # Determine the absolute path
        datatest.to_csv(data_transformed_path)  # Use the absolute path
        print("")
        log(f"Transformation completed!")
        pbar.update(total_rows)  # Update the progress bar to completion

    # Log completion
    logging.info("Data processing completed.")

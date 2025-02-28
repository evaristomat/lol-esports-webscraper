import pandas as pd
import os

# Get the directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct file paths based on the script's location
bets_path = os.path.join(script_dir, 'bets.csv')
results_path = os.path.join(script_dir, 'results.csv')
game_results_path = os.path.join(script_dir, '..', 'database', 'data_transformed.csv')

# Load the CSV files into DataFrames
bets_df = pd.read_csv(bets_path)
game_results_df = pd.read_csv(game_results_path)

# Create an empty DataFrame for the new results CSV
results_df = pd.DataFrame(columns=['date', 'league', 't1', 't2', 'game', 'bet_type', 'bet_line', 'ROI', 'House', 'status'])

# Iterate over each row in the bets DataFrame
for index, bet in bets_df.iterrows():
    # Filter games based on both team combinations and date
    games = game_results_df[
        (game_results_df['date'].str.split(' ').str[0] == bet['date']) &
        (((game_results_df['t1'].str.lower() == bet['t1'].lower()) & (game_results_df['t2'].str.lower() == bet['t2'].lower())) | 
        (game_results_df['t2'].str.lower() == bet['t1'].lower()) & (game_results_df['t1'].str.lower() == bet['t2'].lower()))
    ]

    # Até aqui ok

    # If no games found, continue
    if games.empty:
        print(f"No matching games for {bet['t1']} vs {bet['t2']} on {bet['date']}.")
        continue

    # Iterate over each found game
    for _, game in games.iterrows():
        if bet['bet_type'] == 'FD':
            # Determine the team that got the first dragon
            if game['firstdragon_t1'] == 1:
                team_with_first_dragon = game['t1']
            else:
                team_with_first_dragon = game['t2']
            # Check if the team in bet_line matches the team that got the first dragon
            team_from_bet_line = bet['bet_line'].replace('first_dragon', '').strip()
            if team_with_first_dragon.lower() == team_from_bet_line.lower():
                status = 'win'
                profit = round(bet['odds'] - 1, 2)
            else:
                status = 'loss'
                profit = -1


        elif bet['bet_type'] == 'over':
            if 'total_dragons' in bet['bet_line'] and game['total_dragons'] > float(bet['bet_line'].split()[-1]):
                status = 'win'
                # OK
            elif 'towers' in bet['bet_line'] and game['total_towers'] > float(bet['bet_line'].split()[-1]):
                status = 'win'
            elif 'barons' in bet['bet_line'] and game['total_barons'] > float(bet['bet_line'].split()[-1]):
                status = 'win'   
            elif 'kills' in bet['bet_line'] and game['total_kills'] > float(bet['bet_line'].split()[-1]):
                status = 'win'
            elif 'total_inhibitors ' in bet['bet_line'] and game['total_inhibitors'] > float(bet['bet_line'].split()[-1]):
                status = 'win'
            elif 'game_duration ' in bet['bet_line'] and game['gamelength'] > float(bet['bet_line'].split()[-1]):
                status = 'win'    
            else:
                status = 'loss'

        else:  # For 'under' bets
            if 'total_dragons' in bet['bet_line'] and game['total_dragons'] < float(bet['bet_line'].split()[-1]):
                status = 'win'
            elif 'barons' in bet['bet_line'] and game['total_barons'] < float(bet['bet_line'].split()[-1]):
                status = 'win' 
            elif 'towers' in bet['bet_line'] and game['total_towers'] < float(bet['bet_line'].split()[-1]):
                status = 'win'
            elif 'kills' in bet['bet_line'] and game['total_kills'] < float(bet['bet_line'].split()[-1]):
                status = 'win'
            elif 'total_inhibitors ' in bet['bet_line'] and game['total_inhibitors'] < float(bet['bet_line'].split()[-1]):
                status = 'win'
            elif 'game_duration ' in bet['bet_line'] and game['gamelength'] < float(bet['bet_line'].split()[-1]):
                status = 'win'
            else:
                status = 'loss'

        if status == 'win':
            profit = round(bet['odds'] - 1, 2)
        else:
            profit = -1

        new_row = pd.DataFrame({
            'date': [game['date']],
            'league': [game['league']],
            't1': [game['t1']],
            't2': [game['t2']],
            'game': [game['game']],
            'bet_type': [bet['bet_type']],
            'bet_line': [bet['bet_line']],
            'odds': bet['odds'],
            'ROI': bet['ROI'],
            'House':bet['House'],
            'status': [status],
            'profit': profit
        })
        results_df = pd.concat([results_df, new_row], ignore_index=True)

        # Update bet status based on the first game only
        if game['game'] == 1:
            bets_df.at[index, 'status'] = status

# Load the existing bets DataFrame from the CSV file
existing_bets_df = pd.read_csv(bets_path)

# Concatenate the existing bets DataFrame and the new bets DataFrame
combined_bets_df = pd.concat([existing_bets_df, bets_df], ignore_index=True)

# Ensure teams are in a consistent order for comparison
combined_bets_df['team_combined'] = combined_bets_df[['t1', 't2']].apply(lambda x: ' vs '.join(sorted(x)), axis=1)

# Drop duplicates based on specific columns
combined_bets_df = combined_bets_df.drop_duplicates(subset=['date', 'league', 'team_combined', 'bet_type', 'bet_line', 'ROI', 'odds', 'House'],  keep='last')

# Drop the combined team column if it's not needed
combined_bets_df = combined_bets_df.drop(columns=['team_combined'])

# Save the updated combined bets DataFrame
combined_bets_df.to_csv(bets_path, index=False)

def save_results(results_path, results_df):
    try:
        # Load existing results if available
        existing_results_df = pd.read_csv(results_path)
        combined_results_df = pd.concat([existing_results_df, results_df], ignore_index=True)
        unique_columns = ['date', 'league', 't1', 't2', 'bet_type','bet_line', 'ROI', 'House', 'game']
        # Remove duplicates with the same identifier in the existing data
        updated_results_df = combined_results_df.drop_duplicates(subset=unique_columns, keep='last')
    except FileNotFoundError:
        # If there is no existing file, just save the new results
        results_df.to_csv(results_path, index=False)
        print(f"Results saved to {results_path}")
        return

    # Save the updated results, which now includes the new unique rows
    updated_results_df.to_csv(results_path, index=False)
    print(f"Updated results saved to {results_path}")

save_results(results_path, results_df)
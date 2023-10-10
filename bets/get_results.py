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
results_df = pd.DataFrame(columns=['date', 'league', 't1', 't2', 'game', 'bet_type', 'bet_line', 'ROI', 'status'])

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
            elif 'kills' in bet['bet_line'] and game['total_kills'] > float(bet['bet_line'].split()[-1]):
                status = 'win'
            else:
                status = 'loss'

        else:  # For 'under' bets
            if 'total_dragons' in bet['bet_line'] and game['total_dragons'] < float(bet['bet_line'].split()[-1]):
                status = 'win'
            elif 'towers' in bet['bet_line'] and game['total_towers'] < float(bet['bet_line'].split()[-1]):
                status = 'win'
            elif 'kills' in bet['bet_line'] and game['total_kills'] < float(bet['bet_line'].split()[-1]):
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
            'status': [status],
            'profit': profit
        })
        results_df = pd.concat([results_df, new_row], ignore_index=True)

        # Update bet status based on the first game only
        if game['game'] == 1:
            bets_df.at[index, 'status'] = status

# Save the updated bets DataFrame
bets_df.to_csv(bets_path, index=False)

# Save the results DataFrame
results_df.to_csv(results_path, index=False)

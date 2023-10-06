import pandas as pd

# Assuming you've already loaded your results DataFrame as "results_df"
results_df = pd.read_csv('results.csv')

# Create a new column with the desired groupings
results_df['bet_line_grouped'] = results_df['bet_line'].str.split(' ').str[0]

# Calculate Win Rate
total_bets = len(results_df)
wins = len(results_df[results_df['status'] == 'win'])
win_rate = (wins / total_bets) * 100

# Calculate Profit by Bet Line
profit_by_bet_line = results_df.groupby('bet_line_grouped')['profit'].sum()

# Calculate Total Profit
total_profit = results_df['profit'].sum()

print(f"Win Rate: {win_rate:.2f}%")

print("\nProfit by Bet Line:")
profit_by_bet_line = profit_by_bet_line.apply(lambda x: f"{x:.2f}U")  # Format profit as strings with '%'
print(profit_by_bet_line)

print(f"\nTotal Bets: {total_bets}")  # Display the total number of bets

print(f"\nTotal Profit: {total_profit:.2f}")

# Optionally, you can drop the temporary column if you don't need it anymore
results_df.drop('bet_line_grouped', axis=1, inplace=True)

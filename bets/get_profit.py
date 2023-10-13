import pandas as pd

ROI_TRESHHOLD = 3

# Load data
results_df = pd.read_csv('results.csv')

# Convert the 'ROI' column to numerical format by stripping '%' and converting to float
results_df['ROI'] = results_df['ROI'].str.rstrip('%').astype(float)

# Filter data
filtered_results = results_df[results_df['ROI'] > ROI_TRESHHOLD].copy()

# Group by 'bet_line' and create a new column for this
filtered_results['bet_line_grouped'] = filtered_results['bet_line'].str.split(' ').str[0]

# Calculate win rate
total_bets = len(filtered_results)
wins = len(filtered_results[filtered_results['status'] == 'win'])
win_rate = (wins / total_bets) * 100 if total_bets > 0 else 0  # Handle division by zero

# Calculate profit by bet line
profit_by_bet_line = filtered_results.groupby('bet_line_grouped')['profit'].sum()

# Calculate total profit
total_profit = filtered_results['profit'].sum()

# Calculate average ROI
avg_roi = results_df['ROI'].mean()

# Calculate actual ROI
actual_roi = (total_profit / total_bets) * 100 if total_bets > 0 else 0  # Handle division by zero

# Display results
print(f"Win Rate: {win_rate:.2f}%")
print(f"Average ROI: {avg_roi:.2f}%")
print(f"Actual ROI: {actual_roi:.2f}%")
print("\nProfit by Bet Line:")
for line, profit in profit_by_bet_line.items():
    print(f"{line}: {profit:.2f}U")
print(f"\nTotal Bets: {total_bets}")
print(f"\nTotal Profit: {total_profit:.2f}U")

# Optionally, you can drop the temporary column if you don't need it anymore
filtered_results.drop('bet_line_grouped', axis=1, inplace=True)

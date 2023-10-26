import pandas as pd

def roi_to_units(roi):
    """Convert ROI to units based on the given criteria."""
    if roi <= 10:
        return 0  # no units placed
    elif roi <= 20:
        return 1 
    else:
        return 2

ROI_TRESHHOLD = 10

# Load data
results_df = pd.read_csv('results.csv')

# Convert the 'ROI' column to numerical format by stripping '%' and converting to float
results_df['ROI'] = results_df['ROI'].str.rstrip('%').astype(float)

# Map the ROI values to unit placements and store in a new column
results_df['units'] = results_df['ROI'].apply(roi_to_units)

# Calculate the profit (or loss) for each bet with the units placement
results_df['adjusted_profit'] = results_df['profit'] * results_df['units']

# Calculate backtested total profit
backtested_profit = results_df['adjusted_profit'].sum()

# For original strategy (1 unit every bet) apply the ROI_TRESHHOLD filter
filtered_results = results_df[results_df['ROI'] > ROI_TRESHHOLD].copy()

# Group by 'bet_line' and create a new column for this for both strategies
filtered_results['bet_line_grouped'] = filtered_results['bet_line'].str.split(' ').str[0]
results_df['bet_line_grouped'] = results_df['bet_line'].str.split(' ').str[0]

# Calculate profit by bet line for both strategies
profit_by_bet_line_original = filtered_results.groupby('bet_line_grouped')['profit'].sum()
profit_by_bet_line_backtest = results_df.groupby('bet_line_grouped')['adjusted_profit'].sum()

# Calculate win rate
total_bets = len(filtered_results)
wins = len(filtered_results[filtered_results['status'] == 'win'])
win_rate = (wins / total_bets) * 100 if total_bets > 0 else 0  # Handle division by zero

# Calculate total profit with 1 unit every bet
total_profit = filtered_results['profit'].sum()

# Calculate average ROI
avg_roi = results_df['ROI'].mean()

# Calculate actual ROI
actual_roi = (total_profit / total_bets) * 100 if total_bets > 0 else 0  # Handle division by zero

# Display results
print(f"Win Rate: {win_rate:.2f}%")
print(f"Average ROI: {avg_roi:.2f}%")
print(f"Actual ROI (1 unit every bet): {actual_roi:.2f}%")
print("\nProfit by Bet Line (1 unit every bet):")
for line, profit in profit_by_bet_line_original.items():
    print(f"{line}: {profit:.2f}U")

print("\nProfit by Bet Line (using ROI-based units):")
for line, profit in profit_by_bet_line_backtest.items():
    print(f"{line}: {profit:.2f}U")

print(f"\nTotal Bets (with ROI > {ROI_TRESHHOLD}%): {total_bets}")
print(f"\nTotal Profit (1 unit every bet): {total_profit:.2f}U")
print(f"\nBacktested Profit (using ROI-based units): {backtested_profit:.2f}U")

# Optionally, you can drop the temporary columns if you don't need them anymore
results_df.drop(['units', 'adjusted_profit', 'bet_line_grouped'], axis=1, inplace=True)
filtered_results.drop('bet_line_grouped', axis=1, inplace=True)

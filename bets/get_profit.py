import pandas as pd

def load_and_prepare_data(filepath):
    df = pd.read_csv(filepath)
    df['ROI'] = df['ROI'].str.rstrip('%').astype(float)
    df['date'] = pd.to_datetime(df['date'])
    return df

def calculate_profit_and_stats(df, roi_threshold):
    # Calculate stats for all time
    df['units'] = df['ROI'].apply(roi_to_units)
    df['adjusted_profit'] = df['profit'] * df['units']
    backtested_profit = df['adjusted_profit'].sum()

    filtered_df = df[df['ROI'] > roi_threshold].copy()
    total_bets = len(filtered_df)
    wins = len(filtered_df[filtered_df['status'] == 'win'])
    win_rate = (wins / total_bets) * 100 if total_bets > 0 else 0
    total_profit = filtered_df['profit'].sum()
    avg_roi = filtered_df['ROI'].mean() if total_bets > 0 else 0
    actual_roi = (total_profit / total_bets) * 100 if total_bets > 0 else 0

    backtest_filtered_df = df[df['units'] > 0].copy()
    backtest_total_bets = len(backtest_filtered_df)
    backtest_total_profit = backtest_filtered_df['adjusted_profit'].sum()
    backtest_actual_roi = (backtest_total_profit / backtest_total_bets) * 100 if backtest_total_bets > 0 else 0

    # Calculate stats for the current month
    current_month = pd.to_datetime('today').to_period('M')
    current_month_df = df[df['date'].dt.to_period('M') == current_month]

    current_month_filtered_df = current_month_df[current_month_df['ROI'] > roi_threshold].copy()
    current_month_total_bets = len(current_month_filtered_df)
    current_month_wins = len(current_month_filtered_df[current_month_filtered_df['status'] == 'win'])
    current_month_losses = len(current_month_filtered_df[current_month_filtered_df['status'] == 'loss'])
    current_month_win_rate = (current_month_wins / current_month_total_bets) * 100 if current_month_total_bets > 0 else 0
    current_month_total_profit = current_month_filtered_df['profit'].sum()
    current_month_avg_roi = current_month_filtered_df['ROI'].mean() if current_month_total_bets > 0 else 0

    return {
        'backtested_profit': backtested_profit,
        'total_bets': total_bets,
        'win_rate': win_rate,
        'total_profit': total_profit,
        'avg_roi': avg_roi,
        'actual_roi': actual_roi,
        'backtest_total_bets': backtest_total_bets,
        'backtest_total_profit': backtest_total_profit,
        'backtest_actual_roi': backtest_actual_roi,
        'filtered_df': filtered_df,
        'df': df,
        'current_month_total_bets': current_month_total_bets,
        'current_month_wins': current_month_wins,
        'current_month_losses': current_month_losses,
        'current_month_win_rate': current_month_win_rate,
        'current_month_total_profit': current_month_total_profit,
        'current_month_avg_roi': current_month_avg_roi
    }

def calculate_daily_profits_and_counts(df):
    # Get the current month's period (year and month)
    current_month = df['date'].dt.to_period('M').max()
    # Convert the period to the actual start and end date of the month
    start_date = current_month.start_time
    end_date = current_month.end_time

    # Filter for the current month and exclude pending bets
    completed_bets_df = df[(df['date'] >= start_date) & (df['date'] <= end_date) & (~df['status'].str.contains('pending'))]
    
    # Group by date and calculate the sum of profits and the count of bets for each day
    daily_summary = completed_bets_df.groupby(completed_bets_df['date'].dt.date).agg({
        'profit': 'sum',
        'status': 'count'  # Using the 'status' column to count the number of bets since each row is a bet.
    })
    daily_summary.rename(columns={'status': 'number_of_bets'}, inplace=True)

    return daily_summary

def display_results(stats, daily_summary, ROI_THRESHOLD):
    print(f"\nTotal Bets (with ROI > {ROI_THRESHOLD}%): {stats['total_bets']}")
    print(f"Win Rate: {stats['win_rate']:.2f}%")
    print(f"Average ROI: {stats['avg_roi']:.2f}%")

    print(f"\nTotal Profit (1 unit every bet): {stats['total_profit']:.2f}U")
    print(f"Actual ROI (1 unit every bet): {stats['actual_roi']:.2f}%")
    print(f"\nBacktested Profit (using ROI-based units): {stats['backtested_profit']:.2f}U")
    print(f"Actual ROI (using ROI-based units): {stats['backtest_actual_roi']:.2f}%\n")
    
    print(f"\nMonthly Statistics for the Current Month:")
    print(f"Monthly Profit: {stats['current_month_total_profit']:.2f}U")
    print(f"Total Monthly Bets: {stats['current_month_total_bets']}")
    print(f"Monthly Wins: {stats['current_month_wins']}")
    print(f"Monthly Losses: {stats['current_month_losses']}")
    print(f"Average Monthly ROI: {stats['current_month_avg_roi']:.2f}%")

    print("\nDaily Summary (Profits and Number of Bets):")
    for date, row in daily_summary.iterrows():
        print(f"{date}: {row['profit']:.2f}U, No. bets: {row['number_of_bets']}")

def roi_to_units(roi):
    if roi <= 10:
        return 0
    elif roi <= 20:
        return 1
    else:
        return 2

# Constants
ROI_TRESHHOLD = 0
TELEGRAM = 'bets.csv'
ALL = 'results.csv'

def main():
    all_maps_df = load_and_prepare_data(ALL)    
    stats = calculate_profit_and_stats(all_maps_df, ROI_TRESHHOLD)
    daily_summary = calculate_daily_profits_and_counts(all_maps_df)
    display_results(stats, daily_summary, ROI_TRESHHOLD)

if __name__ == "__main__":
    main()

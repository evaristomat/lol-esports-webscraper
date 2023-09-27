import pandas as pd
from data_loader import DataLoader

class HeadToHeadStatsCalculator:
    def __init__(self, teamname1: str, teamname2: str, data_loader: DataLoader, n: int = 10) -> None:
        self._teamname1 = teamname1
        self._teamname2 = teamname2
        self._n = n
        self._teams_data = data_loader.get_data()
        self._validate_n()
        self._last_n_games = self._get_last_n_games()

    def _validate_n(self) -> None:
        if self._n <= 0 or not isinstance(self._n, int):
            raise ValueError("n should be a positive integer")

    def _get_last_n_games(self) -> pd.DataFrame:
        h2h_games = self._teams_data.query('(t1 == @self._teamname1 and t2 == @self._teamname2) or (t1 == @self._teamname2 and t2 == @self._teamname1)').copy()
        h2h_games['date'] = pd.to_datetime(h2h_games['date'])

        if h2h_games.empty:
            return pd.DataFrame()

        # Convert 'date' column to datetime, if it's not already.
        if h2h_games['date'].dtype == 'O':  # 'O' means object, typical for strings
            h2h_games['date'] = pd.to_datetime(h2h_games['date'])

        # Sort by date in descending order and get the first 'n' rows
        h2h_games_sorted = h2h_games.sort_values(by='date', ascending=False).head(self._n)

        return h2h_games_sorted
    
    def over_dragons_4_5(self):
        count_over_4_5 = 0
        total_games = len(self._last_n_games)

        for index, game in self._last_n_games.iterrows():
            if game['total_dragons'] > 4.5:  # assuming 'total_dragons' is the correct key
                count_over_4_5 += 1

        return (count_over_4_5 / total_games) * 100 if total_games > 0 else 0


    # Other functions (like _calculate_percentage and the specific stats functions) would be similar to the ones in TeamStatsCalculator
    
    def print_last_n_h2h_games(self) -> None:
        if self._last_n_games.empty:
            print(f"No games found between {self._teamname1} and {self._teamname2} in the last {self._n} games.")
        else:
            print(self._last_n_games[['league', 'year', 't1', 't2', 'total_dragons', 'total_kills', 'total_barons', 'total_towers']])

if __name__ == "__main__":
    filename = '../database/data_transformed.csv'  # Adjust this to your actual file path
    team1 = "Team BDS"
    team2 = "Fnatic"
    n = 10  # or any other positive integer

    try:
        data_loader = DataLoader(filename)
        h2h_stats_calculator = HeadToHeadStatsCalculator(team1, team2, data_loader, n)
        h2h_stats_calculator.print_last_n_h2h_games()  # Add more methods calls as needed
    except Exception as e:
        print(f"An error occurred: {e}")


import pandas as pd
from data_loader import DataLoader  # Assuming data_loader.py is in the same directory

class TeamStatsCalculator:
    def __init__(self, teamname: str, data_loader: DataLoader, n: int = 10) -> None:
        self._teamname = teamname
        self._n = n
        self._teams_data = data_loader.get_data()
        self._validate_n()
        self._last_n_games = self._get_last_n_games()

    def _validate_n(self) -> None:
        if self._n <= 0 or not isinstance(self._n, int):
            raise ValueError("n should be a positive integer")

    def _get_last_n_games(self) -> pd.DataFrame:
        team_games = self._teams_data.query('t1 == @self._teamname or t2 == @self._teamname')
        return team_games.tail(self._n) if not team_games.empty else pd.DataFrame()

    def _calculate_percentage(self, condition: pd.Series) -> float:
        if self._last_n_games.empty or self._n == 0:
            return 0
        return (len(self._last_n_games[condition]) / self._n) * 100

    def towers_over_11_5(self) -> float:
        condition = (
            ((self._last_n_games['t1'] == self._teamname) & (self._last_n_games['total_towers'] > 11.5)) |
            ((self._last_n_games['t2'] == self._teamname) & (self._last_n_games['total_towers'] > 11.5))
        )
        return self._calculate_percentage(condition)

    def towers_over_12_5(self) -> float:
        condition = (
            ((self._last_n_games['t1'] == self._teamname) & (self._last_n_games['total_towers'] > 12.5)) |
            ((self._last_n_games['t2'] == self._teamname) & (self._last_n_games['total_towers'] > 12.5))
        )
        return self._calculate_percentage(condition)

    def over_dragons_4_5(self) -> float:
        try:
            return self._calculate_percentage(self._last_n_games['total_dragons'] > 4.5)
        except KeyError:
            return "No odds"


    def total_barons_over_1_5(self) -> float:
        return self._calculate_percentage(self._last_n_games['total_barons'] > 1.5)

    def total_kills_over_threshold(self, total_kills_threshold: float = 27.5) -> float:
        return self._calculate_percentage(self._last_n_games['total_kills'] > total_kills_threshold)

    def print_last_n_games(self) -> None:
        if self._last_n_games.empty:
            print(f"No games found for {self._teamname} in the last {self._n} games.")
        else:
            print(self._last_n_games[['league', 'year', 't1', 't2', 'total_dragons', 'total_kills', 'total_barons', 'total_towers']])

if __name__ == "__main__":
    filename = '../database/data_transformed.csv'
    team = "Team BDS"
    n = 10
    total_kills_threshold = 27.5

    try:
        data_loader = DataLoader(filename)
        team_stats_calculator = TeamStatsCalculator(team, data_loader, n)
        print(f"Towers over 11.5 in last {n} games for {team}: {team_stats_calculator.towers_over_11_5():.2f}%")
        print(f"Towers over 12.5 in last {n} games for {team}: {team_stats_calculator.towers_over_12_5():.2f}%")
        print(f"Total barons over 1.5 in last {n} games for {team}: {team_stats_calculator.total_barons_over_1_5():.2f}%")
        print(f"Dragons over 4.5 in last {n} games for {team}: {team_stats_calculator.over_dragons_4_5():.2f}%")
        print(f"Total kills over {total_kills_threshold} in last {n} games for {team}: {team_stats_calculator.total_kills_over_threshold(total_kills_threshold=total_kills_threshold):.2f}%")
        team_stats_calculator.print_last_n_games()
    except Exception as e:
        print(f"An error occurred: {e}")
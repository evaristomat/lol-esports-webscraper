import pandas as pd
from db_loader import DatabaseLoader  # Assuming data_loader.py is in the same directory

class TeamStatsCalculator:
    def __init__(self, teamname: str, data_loader: DatabaseLoader) -> None:
        self._teamname = teamname
        self._teams_data = data_loader.get_data()
        self._last_n_games = self._get_last_n_games()

    def _validate_n(self) -> None:
        if self._n <= 0 or not isinstance(self._n, int):
            raise ValueError("n should be a positive integer")
    # Last 3 patches limited to 20 games
    def _get_last_n_games(self) -> pd.DataFrame:
        team_games = self._teams_data.query('t1 == @self._teamname or t2 == @self._teamname')
        if team_games.empty:
            return pd.DataFrame()

        patches = team_games['patch'].unique()
        patches.sort()
        recent_patches = patches[-3:] if len(patches) >= 3 else patches
        last_n_games = team_games[team_games['patch'].isin(recent_patches)]
        
        return last_n_games.tail(min(20, len(last_n_games)))  # Here you are still limiting to the last 20 games

    def _calculate_percentage(self, condition: pd.Series) -> float:
        num_games = len(self._last_n_games)
        if num_games == 0:
            return 0
        return (len(self._last_n_games[condition]) / num_games) * 100

    def total_towers_over_threshold(self, towers_threshold: float) -> float:
        if not isinstance(towers_threshold, (int, float)):
            raise ValueError("towers_threshold should be a numeric value")
            
        condition = (
            ((self._last_n_games['t1'] == self._teamname) & (self._last_n_games['total_towers'] > towers_threshold)) |
            ((self._last_n_games['t2'] == self._teamname) & (self._last_n_games['total_towers'] > towers_threshold))
        )
        return self._calculate_percentage(condition)


    def over_dragons(self, dragon_threshold: float) -> float:
        try:
            return self._calculate_percentage(self._last_n_games['total_dragons'] > dragon_threshold)
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
            print(self._last_n_games[['league', 'year','patch', 't1', 't2', 'total_dragons', 'total_kills', 'total_barons', 'total_towers']])

if __name__ == "__main__":
    filename = '../database/data_transformed.csv'
    team = "Team BDS"

    try:
        data_loader = DatabaseLoader(filename)
        team_stats_calculator = TeamStatsCalculator(team, data_loader)
        num_games = len(team_stats_calculator._last_n_games)
        print(f"Towers over 11.5 in last {num_games} games for {team}: {team_stats_calculator.towers_over_11_5():.2f}%")
        print(f"Towers over 12.5 in last {num_games} games for {team}: {team_stats_calculator.towers_over_12_5():.2f}%")
        print(f"Total barons over 1.5 in last {num_games} games for {team}: {team_stats_calculator.total_barons_over_1_5():.2f}%")
        print(f"Dragons over {4.5} in last {num_games} games for {team}: {team_stats_calculator.over_dragons(4.5):.2f}%")
        print(f"Total kills over {27.5} in last {num_games} games for {team}: {team_stats_calculator.total_kills_over_threshold(27.5):.2f}%")
        team_stats_calculator.print_last_n_games()
    except Exception as e:
        print(f"An error occurred: {e}")

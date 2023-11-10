import pandas as pd
from db_loader import DatabaseLoader

MAX_GAMES = 20
RECENT_PATCHES_COUNT = 3

class TeamNameError(Exception):
    """Custom exception class to handle errors with team names."""
    pass

class TeamStatsCalculator:
    def __init__(self, teamname: str, data_loader: DatabaseLoader) -> None:
        self._teamname = teamname
        self._teams_data = data_loader.get_data()

         # Check if the team name exists in the database
        if not self._is_teamname_in_database():
            raise TeamNameError(f"Team name '{teamname}' not found in the database.")
                                
        self._last_n_games = self._get_last_n_games()

    def _is_teamname_in_database(self) -> bool:
        """Check if the team name exists in the database."""
        return any(self._teams_data['t1'].eq(self._teamname) | self._teams_data['t2'].eq(self._teamname))
    
    def _get_last_n_games(self) -> pd.DataFrame:
        team_games = self._teams_data.query('t1 == @self._teamname or t2 == @self._teamname')
        if team_games.empty:
            return pd.DataFrame()

        patches = sorted(team_games['patch'].unique())
        recent_patches = patches[-RECENT_PATCHES_COUNT:]
        last_n_games = team_games[team_games['patch'].isin(recent_patches)]
        
        return last_n_games.tail(min(MAX_GAMES, len(last_n_games)))

    def _calculate_percentage(self, condition: pd.Series) -> float:
        num_games = len(self._last_n_games)
        if num_games == 0:
            return 0.0
        return (len(self._last_n_games[condition]) / num_games) * 100

    # Global Methods
    def total_towers_over_threshold(self, towers_threshold: float) -> float:
        condition = self._last_n_games['total_towers'] > towers_threshold
        return self._calculate_percentage(condition)
    
    def over_dragons(self, dragon_threshold: float) -> float:
        condition = self._last_n_games['total_dragons'] > dragon_threshold
        return self._calculate_percentage(condition)

    def over_barons(self, baron_threshold: float) -> float:
        condition = self._last_n_games['total_barons'] > baron_threshold
        return self._calculate_percentage(condition)

    def total_kills_over_threshold(self, total_kills_threshold: float = 27.5) -> float:
        condition = self._last_n_games['total_kills'] > total_kills_threshold
        return self._calculate_percentage(condition)
    
    def game_duration(self, game_duration: float) -> float:
        condition = self._last_n_games['gamelength'] > game_duration
        return self._calculate_percentage(condition)
    
    def total_inhibitors(self, total_inhibitors: float) -> float:
        condition = self._last_n_games['total_inhibitors'] > total_inhibitors
        return self._calculate_percentage(condition)
    
    # Team Based Methods
    def total_fd(self) -> float:
        num_games = len(self._last_n_games)
        if num_games == 0:
            return 0.0

        games_where_team_got_first_dragon_as_t1 = self._last_n_games[(self._last_n_games['t1'] == self._teamname) & (self._last_n_games['firstdragon_t1'] == 1.0)]
        games_where_team_got_first_dragon_as_t2 = self._last_n_games[(self._last_n_games['t2'] == self._teamname) & (self._last_n_games['firstdragon_t2'] == 1.0)]
        
        total_games_with_first_dragon = len(games_where_team_got_first_dragon_as_t1) + len(games_where_team_got_first_dragon_as_t2)
        
        return (total_games_with_first_dragon / num_games) * 100

    def print_last_n_games(self) -> None:
        if self._last_n_games.empty:
            print(f"No games found for {self._teamname}.")
        else:
            #print(self._last_n_games[['league', 'year','patch', 't1', 't2','total_kills', 'total_dragons','firstdragon_t1', 'total_barons', 'total_towers']])
            print(self._last_n_games[['league', 'year','patch', 't1', 't2','firstdragon_t1']])    
    def get_last_n_games_count(self):
        return len(self._last_n_games)

if __name__ == "__main__":
    filename = '../database/data_transformed.csv'
    team = "Back2TheGame Outlaws"

    try:
        data_loader = DatabaseLoader(filename)
        team_stats_calculator = TeamStatsCalculator(team, data_loader)
        num_games = team_stats_calculator.get_last_n_games_count()
        print("Games from last 3 patches")
        print(f"Towers over 11.5 in last {num_games} games for {team}: {team_stats_calculator.total_towers_over_threshold(11.5):.2f}%")
        print(f"Towers over 12.5 in last {num_games} games for {team}: {team_stats_calculator.total_towers_over_threshold(12.5):.2f}%")
        print(f"Total barons over 1.5 in last {num_games} games for {team}: {team_stats_calculator.over_barons(1.5):.2f}%")
        print(f"Dragons over 4.5 in last {num_games} games for {team}: {team_stats_calculator.over_dragons(4.5):.2f}%")
        print(f"Total kills over 21.5 in last {num_games} games for {team}: {team_stats_calculator.total_kills_over_threshold(21.5):.2f}%")
        print(f"First Dragon in last {num_games} games for {team}: {team_stats_calculator.total_fd():.2f}%")
        print(f"Game Duration o30.5 in last {num_games} games for {team}: {team_stats_calculator.game_duration(30.5):.2f}%")
        print(f"Total over 1.5 inhibitors in last {num_games} games for {team}: {team_stats_calculator.total_inhibitors(1.5):.2f}%")
        team_stats_calculator.print_last_n_games()

    except TeamNameError as e:
            print(f"An error occurred: {e}")
    except Exception as e:
            print(f"An unexpected error occurred: {e}")
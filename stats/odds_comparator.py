import datetime
from team_stats_calculator import TeamStatsCalculator
from db_loader import DatabaseLoader
from match_odds import MatchOdds
import json

class OddsComparator:
    def __init__(self, filename, game_data):
        self.filename = filename
        self.game_data = game_data

    @staticmethod
    def calculate_roi(probability, odds):
        ev = probability * (odds - 1) - (1 - probability)
        return (ev * 100)  # assuming cost is 1

    @property
    def game_date(self):
        timestamp = self.game_data["overview"]["game_date"]
        date = datetime.datetime.utcfromtimestamp(timestamp)
        return date.strftime('%Y-%m-%d')
    
    @property
    def game_league(self):
        league = self.game_data["overview"]["league"]
        return league

    def _compare(self, compare_func, line_key, line_value_func):
        game = MatchOdds(self.game_data)
        data_loader = DatabaseLoader(self.filename)
        home_team, away_team = game.home_team(), game.away_team()

        try:
            combined_stats = 0
            line_value = line_value_func()[line_key]

            for team in [home_team, away_team]:
                team_all_stats = TeamStatsCalculator(team, data_loader)
                stats = compare_func(team_all_stats, line_value)

                if stats == "No odds":
                    print(f"No odds available for {team}'s {line_key} stats.")
                    continue

                combined_stats += stats / 200  # Same as (stats / 100) / 2

            line_match = line_value_func()

            if combined_stats > 0:
                roi_over_combined = self.calculate_roi(combined_stats, line_match['over'])
                roi_under_combined = self.calculate_roi(1 - combined_stats, line_match['under'])

                best_bet, best_roi = ('over', roi_over_combined) if roi_over_combined > roi_under_combined else ('under', roi_under_combined)

                if best_roi > 0:
                    return {
                        "date": self.game_date,
                        "league": self.game_league,
                        "t1": home_team,
                        "t2": away_team,
                        line_key: line_value,
                        "bet": best_bet,
                        "ROI": f"{best_roi:.2f}%",
                        "odds": line_match[best_bet]
                    }
        except Exception as e:
            return None

    def compare_dragon(self):
        return self._compare(
            lambda team_stats, line_value: team_stats.over_dragons(line_value),
            'total_dragons',
            lambda: MatchOdds(self.game_data).total_dragons()
        )

    def compare_tower(self):
        return self._compare(
            lambda team_stats, line_value: team_stats.total_towers_over_threshold(line_value),
            'total_towers',
            lambda: MatchOdds(self.game_data).total_towers()
        )

if __name__ == "__main__":
    filename = '../database/data_transformed.csv'
    
    with open(r'..\data\2023-09-26\games_Bet365Webscraper.json', 'r') as file:
        games = json.load(file)
    
    game_data = games[4]
    timestamp = game_data['overview']['game_date']
    date = datetime.datetime.utcfromtimestamp(timestamp)
    formatted_date = date.strftime('%Y-%m-%d')
    print(formatted_date)
    
    comparator = OddsComparator(filename, game_data)
    best = comparator.compare_dragon()
    print(best)
    print("\n")
    best = comparator.compare_tower()
    print(best)

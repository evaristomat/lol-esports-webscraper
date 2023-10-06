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
            #print(f"Category: {line_key}")            

            if line_key == 'first_dragon':
                team_stats_dict = {}
                # Calculate stats (probability) for each team
                for team in [home_team, away_team]:
                    team_all_stats = TeamStatsCalculator(team, data_loader)
                    stats = team_all_stats.total_fd()

                    if stats == "No odds":
                        print(f"No odds available for {team}'s {line_key} stats.")
                        continue

                    team_stats_dict[team] = stats / 100

                dragon_odds = game.first_dragon()
                roi_home = self.calculate_roi(team_stats_dict[home_team], dragon_odds[home_team])
                roi_away = self.calculate_roi(team_stats_dict[away_team], dragon_odds[away_team])

                best_team, best_roi = (home_team, roi_home) if roi_home > roi_away else (away_team, roi_away)

                if best_roi > 0:
                    return {
                        "date": self.game_date,
                        "league": self.game_league,
                        "t1": home_team,
                        "t2": away_team,
                        line_key: best_team,
                        "bet": "FD",
                        "ROI": f"{best_roi:.2f}%",
                        "odds": dragon_odds[best_team]
                    }
                
            else:
                combined_stats = 0    
                line_value_dict = line_value_func()[line_key]
                for team in [home_team, away_team]:
                    team_all_stats = TeamStatsCalculator(team, data_loader)
                    stats = compare_func(team_all_stats, line_value_dict)

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
                            line_key: line_value_dict,
                            "bet": best_bet,
                            "ROI": f"{best_roi:.2f}%",
                            "odds": line_match[best_bet]
                        }
        except Exception as e:
            print(f"Error in _compare for {line_key}: {e}")
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
    
    def compare_kills(self):
        return self._compare(
            lambda team_stats, line_value: team_stats.total_kills_over_threshold(line_value),
            'total_kills',
            lambda: MatchOdds(self.game_data).total_kills()
        )
    
    def compare_first_drake(self):
        return self._compare(
            lambda team_stats, line_value: team_stats.total_fd(),
            'first_dragon',
            lambda: MatchOdds(self.game_data).first_dragon()
        )    


if __name__ == "__main__":
    filename = '../database/data_transformed.csv'
    
    with open(r'..\data\2023-10-03\games_DafabetWebscraper.json', 'r') as file:
        games = json.load(file)
    
    game_data = games[0]
    timestamp = game_data['overview']['game_date']
    date = datetime.datetime.utcfromtimestamp(timestamp)
    formatted_date = date.strftime('%Y-%m-%d')
    print(formatted_date)
    
    comparator = OddsComparator(filename, game_data)
    # best = comparator.compare_dragon()
    # print(best)
    # best = comparator.compare_tower()
    # print(best)
    # best = comparator.compare_kills()
    # print(best)
    best = comparator.compare_first_drake()
    print(best)
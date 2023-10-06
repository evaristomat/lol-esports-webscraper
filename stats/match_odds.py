import json
class MatchOdds:
    """
    A class to represent match odds extracted from a JSON object.
    
    Attributes
    ----------
    game_json : dict
        A dictionary containing game-related data extracted from a JSON object.
    
    Methods
    -------
    home_team():
        Returns the home team.
    away_team():
        Returns the away team.
    winner():
        Returns the winner of the game.
    first_blood():
        Returns the team that achieved the first blood.
    first_baron():
        Returns the team that killed the first baron.
    first_inhib():
        Returns the team that destroyed the first inhibitor.
    kill_handicap():
        Returns the kill handicap information.
    total_kills():
        Returns the total kills information.
    total_towers():
        Returns the total towers information.
    total_dragons():
        Returns the total dragons information.
    total_barons():
        Returns the total barons information.
    total_inhibitors():
        Returns the total inhibitors information.
    
    Note
    ----
    The _get_category_score and _get_category_handicap methods are
    utility methods used internally to extract specific category score
    and handicap information respectively from the game_json.
    """
    def __init__(self, game_json):
        self.game_json = game_json

    def home_team(self):
        return self.game_json['overview']['home_team']

    def away_team(self):
        return self.game_json['overview']['away_team']
        
    def get_league(self):
        return self.game_json['overview']['league']

    def _get_category_score(self, category):
        if not self.game_json.get(category) or not self.game_json[category]:
            return {
                self.home_team(): None,
                self.away_team(): None
            }
        return {
            self.home_team(): self.game_json[category][0].get('home_team_score', None),
            self.away_team(): self.game_json[category][0].get('away_team_score', None)
        }
    
    def _get_category_handicap(self, category):
        if not self.game_json.get(category) or not self.game_json[category]:
            return {
                'handicap': None,
                'over': None,
                'under': None
            }
        return {
            category: self.game_json[category][0].get('total_amount', None),
            'over': self.game_json[category][0].get('home_team_score', None),
            'under': self.game_json[category][0].get('away_team_score', None)
        }

    def winner(self):
        return self._get_category_score('winner')

    def first_blood(self):
        return self._get_category_score('first_blood')

    def first_baron(self):
        return self._get_category_score('first_kill_baron')

    def first_dragon(self):
        return self._get_category_score('first_dragon')
    
    def first_inhib(self):
        return self._get_category_score('first_destroy_inhibitor')

    def kill_handicap(self):
        return self._get_category_handicap('kill_handicap')
    
    def total_kills(self):
        return self._get_category_handicap('total_kills')

    def total_towers(self):
        return self._get_category_handicap('total_towers')

    def total_dragons(self):
        return self._get_category_handicap('total_dragons')

    def total_barons(self):
        return self._get_category_handicap('total_barons')

    def total_inhibitors(self):
        return self._get_category_handicap('total_inhibitors')


if __name__ == "__main__": 
    with open(r'..\data\2023-10-03\games_DafabetWebscraper.json', 'r') as file:
        games = json.load(file)
    
    game_data = games[0]  # or whatever index or method you're using to select the game
    test = MatchOdds(game_data)
    print(test.first_dragon())
    # '{'total_dragons': 4.5, 'over': 1.57, 'under': 2.25}'
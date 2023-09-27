class GameStats:
    def __init__(self, game_json):
        self.game_json = game_json

    def home_team(self):
        return self.game_json['overview']['home_team']

    def away_team(self):
        return self.game_json['overview']['away_team']

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

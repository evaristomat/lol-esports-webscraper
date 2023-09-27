import json
from team_stats_calculator import TeamStatsCalculator
from data_loader import DataLoader
from game_stats import GameStats
from head2head_calc import HeadToHeadStatsCalculator


class OddsComparator:
    def __init__(self, filename, game_data, n=10):
        self.filename = filename
        self.game_data = game_data
        self.n = n
    
    def calculate_roi(self, probability, odds):
        ev = probability * (odds - 1) - (1 - probability)
        expected_roi = (ev / 1) * 100  # assuming cost is 1
        return expected_roi
    
    def compare(self):
        # Load game stats
        game = GameStats(self.game_data)

        home_team = game.home_team()
        away_team = game.away_team()

        # Calculate the head-to-head stats
        data_loader = DataLoader(self.filename)
        h2h_stats_calculator = HeadToHeadStatsCalculator(home_team, away_team, data_loader, self.n)
        h2h_stats = h2h_stats_calculator._get_last_n_games()

        # Calculate the head-to-head dragons stats, and handle "No odds" case
        h2h_dragons_stats = h2h_stats_calculator.over_dragons_4_5()
        if h2h_dragons_stats == "No odds":
            print("No odds available for head-to-head dragons stats.")
            return

        h2h_dragons_stats = h2h_dragons_stats / 100  # Converting to a probability

        combined_dragons_stats = 0
        # Initialize dragons_game with default values
        dragons_game = {'total_dragons': 0, 'over': 0, 'under': 0}
        
        # Perform comparison and Calculate ROI for both home and away team
        for team in [game.home_team(), game.away_team()]:
            # Load team stats
            data_loader = DataLoader(self.filename)
            team_stats_calculator = TeamStatsCalculator(team, data_loader, self.n)

            dragons_stats = team_stats_calculator.over_dragons_4_5()
            if dragons_stats == "No odds":
                print(f"No odds available for {team}'s dragons stats.")
                continue  # Skip this team and continue with the other team

            dragons_stats = dragons_stats / 100  # Converting to a probability
            combined_dragons_stats += dragons_stats / 2  # Averaging the stats of both teams

            dragons_game = game.total_dragons()

            roi_over = self.calculate_roi(dragons_stats, dragons_game['over'])
            roi_under = self.calculate_roi(1 - dragons_stats, dragons_game['under'])

            # Print the comparison results for individual team
            print(f"{team} Stats:")
            print(f"Dragons Stats for over 4.5: {dragons_stats * 100:.2f}%")
            print(f"Total Dragons: {dragons_game['total_dragons']}")
            print(f"Total Dragons over odds: {dragons_game['over']}")
            print(f"Total Dragons under odds: {dragons_game['under']}")
            print(f"Expected ROI for Over 4.5 Dragons: {roi_over:.2f}%")
            print(f"Expected ROI for Under 4.5 Dragons: {roi_under:.2f}%")
            print("\n")

        # Calculate and Print combined dragons stats
        if combined_dragons_stats > 0:  # To ensure that it is not zero due to "No odds" for both teams
            roi_over_combined = self.calculate_roi(combined_dragons_stats, dragons_game['over'])
            roi_under_combined = self.calculate_roi(1 - combined_dragons_stats, dragons_game['under'])
            
            # Print the combined comparison results
            print(f"Match Dragons Stats between {home_team} and {away_team} for over 4.5: {combined_dragons_stats * 100:.2f}%")
            print(f"Expected ROI for Over 4.5 Dragons (Combined): {roi_over_combined:.2f}%")
            print(f"Expected ROI for Under 4.5 Dragons (Combined): {roi_under_combined:.2f}%")
            print("\n")

        # Print head-to-head stats
        print(f"Head-to-Head Stats between {home_team} and {away_team}:")
        print(f"Dragons Stats for over 4.5: {h2h_dragons_stats * 100:.2f}%")
        roi_over_h2h = self.calculate_roi(h2h_dragons_stats, dragons_game['over'])
        roi_under_h2h = self.calculate_roi(1 - h2h_dragons_stats, dragons_game['under'])
        print(f"Expected ROI for Over 4.5 Dragons (H2H): {roi_over_h2h:.2f}%")
        print(f"Expected ROI for Under 4.5 Dragons (H2H): {roi_under_h2h:.2f}%")


if __name__ == "__main__":
    filename = '../database/data_transformed.csv'
    n = 10
    
    with open(r'..\data\2023-09-26\games_Bet365Webscraper.json', 'r') as file:
        games = json.load(file)
    
    game_data = games[4]  # or whatever index or method you're using to select the game
    
    comparator = OddsComparator(filename, game_data, n)
    comparator.compare()

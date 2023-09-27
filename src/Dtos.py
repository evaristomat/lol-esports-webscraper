import hashlib
from dataclasses import dataclass
from datetime import date, datetime
from typing import Union, List

from dataclasses_json import dataclass_json, config


# Missing values will be -1
@dataclass_json
@dataclass
class StatDto:
    total_amount: float
    home_team_score: float
    away_team_score: float

    def __repr__(self):
        return (f"\n   Amount: {self.total_amount}\n   Home Odds: {self.home_team_score}"
                f"\n   Away Odds: {self.away_team_score}")

    def __str__(self):
        return (f"\n   Amount: {self.total_amount}\n   Home Odds: {self.home_team_score}"
                f"\n   Away Odds: {self.away_team_score}")

    def __hash__(self):
        return hash((self.total_amount, self.home_team_score, self.away_team_score))


@dataclass_json
@dataclass
class GameOverviewDto:
    game_date: date
    url: str
    league: str
    home_team: str
    away_team: str

    def __hash__(self):
        data = f"{self.game_date}{self.home_team}{self.away_team}"
        return int(hashlib.sha256(data.encode()).hexdigest(), 16)


@dataclass_json
@dataclass
class GameDetailDto:
    overview: GameOverviewDto
    winner: List[StatDto]
    first_blood: List[StatDto]
    first_kill_baron: List[StatDto]
    first_destroy_inhibitor: List[StatDto]
    kill_handicap: List[StatDto]
    total_kills: List[StatDto]
    total_towers: List[StatDto]
    total_dragons: List[StatDto]
    total_barons: List[StatDto]
    total_inhibitors: List[StatDto]

    def pretty_print(self):
        return (f"Game Date: {datetime.utcfromtimestamp(self.overview.game_date).strftime('%d, %b %Y')}"
                f"\nLeague: {self.overview.league}\nHome Team: {self.overview.home_team}"
                f"\nAway Team: {self.overview.away_team}\nUrl: {self.overview.url}\n\nStats:"
                f"\nWinner: {self.winner}\nFirst Blood: {self.first_blood}\nFirst Kill Baron: {self.first_kill_baron}"
                f"\nFirst Destroy Inhibitor: {self.first_destroy_inhibitor}\nKill Handicap: {self.kill_handicap}"
                f"\nTotal Kills: {self.total_kills}\nTotal Towers: {self.total_towers}\nTotal Dragons: {self.total_dragons}"
                f"\nTotal Barons: {self.total_barons}\nTotal Inhibitors: {self.total_inhibitors}")

    def __hash__(self):
        return hash(self.overview)


def date_converter(value):
    return date.fromisoformat(value)

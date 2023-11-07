import re
import logging
from datetime import datetime
from typing import List, Dict

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.Dtos import GameDetailDto, GameOverviewDto, StatDto
from src.ScrapingService import Webscraper
from src.Utils import ScrollBox, parse_float, remove_duplicates

# Setting up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

extract_number_regex = "[^0-9\-+]"

# Variables for each stat name
winner_stat_name = "Money Line - Mapa 1"
first_blood_stat_name = "(Mapa 1) 1º sangue"
first_kill_baron_stat_name = "(Mapa 1) 1º barão"
first_destroy_inhibitor_stat_name = "(Mapa 1) 1º inibidor"
total_kills_stat_name = "Total (Mortes) – Mapa 1"
total_barons_stat_name = "(Mapa 1) Total de barões mortos"
total_towers_stat_name = "(Mapa 1) Total de torres destruídas"
kill_handicap_stat_name = "Handicap (Mortes) – Mapa 1"
total_dragons_stat_name = "(Mapa 1) Total de dragões elementais mortos"
total_inhibitors_stat_name = "YOUR_STRING_HERE_FOR_TOTAL_INHIBITORS"
tower_handicap_stat_name = "(Mapa 1) Handicap de Torres"
first_tower_stat_name = "(Mapa 1) 1ª Torre"
first_dragon_stat_name = "(Mapa 1) 1º Dragão"
duration_map_stat_name = "(Mapa 1) Duração do jogo"

interested_stats = {
    winner_stat_name,
    first_blood_stat_name,
    first_kill_baron_stat_name,
    first_destroy_inhibitor_stat_name,
    total_kills_stat_name,
    total_barons_stat_name,
    total_towers_stat_name,
    kill_handicap_stat_name,
    total_dragons_stat_name,
    total_inhibitors_stat_name,
    duration_map_stat_name,
    tower_handicap_stat_name,
    first_tower_stat_name,
    first_dragon_stat_name
}

def extract_value_from_label(label: str) -> float:
    """
    Extract the numeric value from the given label.
    Expected formats: "Mais de 31 Minutos", "Mais de 4.5 Dragons", "Mais de 12.5 Torres"
    Returns the numeric value as a float or -1 if no match found.
    """
    match = re.search(r'(\d+(\.\d+)?)', label)
    if match:
        return float(match.group(1))
    else:
        logging.error("Failed to extract value from label: %s", label)
        return -1
    
def request_matchups():
    url = "https://guest.api.arcadia.pinnacle.com/0.1/sports/12/matchups?withSpecials=false&brandId=0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
        "Accept": "application/json",
        "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, utf-8",
        "Referer": "https://www.pinnacle.com/",
        "Content-Type": "application/json",
        "X-API-Key": "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R",
        "X-Device-UUID": "47c63eb4-db77bde8-11eade4e-3e26473b",
        "Origin": "https://www.pinnacle.com",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Host": "guest.api.arcadia.pinnacle.com",
    }
    logging.debug("Sending request to %s", url)
    return requests.get(url, headers=headers).json()


class PinnacleWebscraper(Webscraper):
    @staticmethod
    def get_url() -> str:
        return "https://www.pinnacle.com/pt/esports/games/league-of-legends/matchups"

    def fetch_games(self) -> List[GameDetailDto]:
        logging.debug("Sending matchups request")
        data = request_matchups()
        lol_matchups = list(
            filter(lambda x: "League of Legends" in x["league"]["name"], data)
        )
        logging.debug("Found %d lol related matchups", len(lol_matchups))
        dtos: List[GameDetailDto] = []
        
        for matchup in lol_matchups:
            logging.debug("Processing matchup ID: %s", matchup['id'])
            if matchup["status"] != "pending":
                continue

            league = matchup["league"]["name"]
            home_team = list(
                filter(lambda x: x["alignment"] == "home", matchup["participants"])
            )[0]["name"]
            away_team = list(
                filter(lambda x: x["alignment"] == "away", matchup["participants"])
            )[0]["name"]

            date = datetime.strptime(matchup["startTime"], "%Y-%m-%dT%H:%M:%SZ")
            self.driver.get(
                f"https://www.pinnacle.com/pt/esports/league-of-legends-emea-masters/orbit-anonymo-vs"
                f"-bisons/{matchup['id']}/#all"
            )
            self.timeout()

            logging.debug("Getting Stats")
            dtos.append(
                self.collect_detail_dto(
                    GameOverviewDto(
                        date, self.driver.current_url, league, home_team, away_team
                    )
                )
            )
            logging.debug("Match collected")
            logging.debug("DTOs: %s", dtos)
        return dtos

    def get_stats(self, element: WebElement) -> Dict[str, List[StatDto]]:
        logging.debug("Started")
        stats: Dict[str, List[StatDto]] = {}

        stats_to_click = self.driver.find_elements(By.XPATH,
        "//div[contains(@class,'style_marketGroups___6K0n')]/div[.//span[contains(text(), '(Mapa 1)')]]")
        
        for stat in stats_to_click:
            if stat.get_attribute("data-collapsed"):
                try:
                    stat.click()
                except Exception as e:
                    break
                self.timeout()

            # Find the stat name
            stat_name = stat.find_element(By.CSS_SELECTOR, "div.style_title__2wOdP > span").text
            
            # Check if stat_name is one of the interested stats
            if stat_name not in interested_stats:
                continue

            logging.debug(f"Element, {stat_name}")
            teams = list(
                map(
                    lambda x: parse_float(x.text),
                    stat.find_elements(
                        By.XPATH,
                        "./div[@class='style_content__23pgc "
                        "collapse-content']/div/div/div/button"
                        "/span[2]",
                    ),
                )
            )
            logging.debug("teams: %s", teams)
            labels = list(
                map(
                    lambda x: x.text,
                    stat.find_elements(
                        By.XPATH,
                        "./div[@class='style_content__23pgc "
                        "collapse-content']/div/div/div/button"
                        "/span[1]",
                    ),
                )
            )
            logging.debug("labels: %s", labels)
            content = list(zip(teams, labels))
            pairwise = [[content[i], content[i + 1]] for i in range(0, len(content), 2)]
            if stat_name not in stats:
                stats[stat_name] = []

            for home, away in pairwise:
                value = -1
                if ("Acima" in home[1] or "Mais" in home[1]) or (
                    not re.match(extract_number_regex, home[1])
                    and not re.match(extract_number_regex, away[1])
                ):
                    if "Minutos" in home[1]:
                        value = extract_value_from_label(home[1])
                    else:
                        try:
                            value = abs(parse_float(re.sub(extract_number_regex, "", home[1]))) / 10
                        except ValueError:
                            logging.error("Failed to parse float value from string: %s", home[1])

                stats[stat_name].append(StatDto(value, home[0], away[0]))
        return remove_duplicates(stats)

    def collect_detail_dto(self, overview_dto: GameOverviewDto) -> GameDetailDto:
        stats: Dict[str, List[StatDto]] = ScrollBox(
            lambda: self.find_element(By.TAG_NAME, "html")
        ).collect(self.driver, self.get_stats)

        return GameDetailDto(
            overview=overview_dto,
            winner=stats.get(winner_stat_name, []),
            first_blood=stats.get(first_blood_stat_name, []),
            first_kill_baron=stats.get(first_kill_baron_stat_name, []),
            first_destroy_inhibitor=stats.get(first_destroy_inhibitor_stat_name, []),
            total_kills=stats.get(total_kills_stat_name, []),
            total_barons=stats.get(total_barons_stat_name, []),
            total_towers=stats.get(total_towers_stat_name, []),
            kill_handicap=stats.get(kill_handicap_stat_name, []),
            total_dragons=stats.get(total_dragons_stat_name, []),
            total_inhibitors=stats.get(total_inhibitors_stat_name, []),
            game_duration=stats.get(duration_map_stat_name, []),
            tower_handicap=stats.get(tower_handicap_stat_name, []),
            first_tower=stats.get(first_tower_stat_name, []),
            first_dragon=stats.get(first_dragon_stat_name, [])
        )

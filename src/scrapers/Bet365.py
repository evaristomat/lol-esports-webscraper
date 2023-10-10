import subprocess
import tempfile
import time
from datetime import datetime
from datetime import time as time_parser
from typing import List, Type, Dict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from src.Dtos import GameDetailDto, GameOverviewDto, StatDto
from src.ScrapingService import Webscraper
from src.Utils import parse_float, try_get_element_text, read_stamp, click_element

winner_stat_name = "Vencedor do Mapa 1"
total_inhibitors_stat_name = "Total de Inibidores"
total_dragons_stat_name = "Total de Dragões"
kill_handicap_stat_name = "Kill - Handicap"
total_towers_stat_name = "Total de Torres"
total_barons_stat_name = "Total de Barões"
total_kills_stat_name = "Total de Kills"
first_destroy_inhibitor_stat_name = "Destruir Inibidor"
first_kill_baron_stat_name = "Matar Barão"
first_blood_stat_name = "First Blood"
money_line = "Moneyline"
duration_map_stat_name = "Mapa 1 - Duração do Mapa - 2 Opções"

browser_redirect_wait = 1
chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"


def open_url(url: str) -> webdriver.Chrome:
    print(f"[DEBUG] Opening anti bot browser")

    temp_user_data_dir = tempfile.mkdtemp(prefix="chrome_user_data_")
    chrome_cmd = [
        chrome_path,
        "--no-sandbox",
        "--remote-debugging-port=9222",
        "--disable-dbus",
        "--disable-fre",
        "--no-default-browser-check",
        "--no-first-run",
        f"--user-data-dir={temp_user_data_dir}",
        url,
    ]
    subprocess.Popen(chrome_cmd, shell=True)

    time.sleep(10)
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    return webdriver.Chrome(options=chrome_options)


def create_detail_dto(url: str, overview_dto: GameOverviewDto) -> GameDetailDto:
    time.sleep(browser_redirect_wait)

    # Tricking bet365 again
    driver = open_url(url + "I2/")
    time.sleep(browser_redirect_wait)

    stats: Dict[str, List[StatDto]] = {}

    def get_stat(name) -> StatDto:
        if name not in stats:
            stats[name] = [StatDto(-1, -1, -1)]
        return stats[name][0]

    stat_elements = driver.find_elements(By.CLASS_NAME, "gl-MarketGroup")
    for stat_element in stat_elements:
        title = stat_element.find_element(
            By.CLASS_NAME, "gl-MarketGroupButton_Text"
        ).text
        stat_groups = stat_element.find_elements(
            By.CSS_SELECTOR, ".gl-MarketGroupContainer > div > div"
        )

        # Teste
        if title == "Mapa 1 - Duração do Mapa - 2 Opções":
            try:
                # Extract the duration threshold (e.g. 29:30)
                duration_threshold_str = stat_element.find_element(By.XPATH, './/div[contains(@class, "srb-ParticipantLabelCentered_Name")]').text
                duration_to_float = lambda s: float(s.split(':')[0]) + float(s.split(':')[1])/60
                duration_threshold = duration_to_float(duration_threshold_str)   

                # Extract the "Mais de ou Exatamente" odds 
                over_odds = float(stat_element.find_element(By.XPATH, './/div[contains(text(), "Mais de ou Exatamente")]/following-sibling::div/span').text)

                # Extract the "Menos de" odds
                under_odds = float(stat_element.find_element(By.XPATH, './/div[contains(text(), "Menos de")]/following-sibling::div/span').text)
                
                game_duration_stat = StatDto(
                    total_amount=duration_threshold, 
                    home_team_score=over_odds, 
                    away_team_score=under_odds
                )
                stats[duration_map_stat_name] = [game_duration_stat]

                continue  # skip the rest of the loop for this stat and move on to the next

            except Exception as e:
                print(f"Failed to extract {title} stat. Error: {e}")
        # Teste

        labels = []
        table_index = 0
        home_team = True
        # Parsing multi state table
        for group in stat_groups:
            clazz = group.get_attribute("class")

            odds = parse_float(
                try_get_element_text(
                    group,
                    By.CLASS_NAME,
                    "srb-ParticipantCenteredStackedMarketRow_Odds",
                    "-1",
                )
            )
            handicap = parse_float(
                try_get_element_text(
                    group,
                    By.CLASS_NAME,
                    "srb-ParticipantCenteredStackedMarketRow_Handicap",
                    "-1",
                )
            )

            if "gl-ParticipantBorderless" in clazz:
                team_value = parse_float(
                    group.find_elements(By.TAG_NAME, "span")[1].text
                )

                stat = get_stat(title)
                if stat.home_team_score == -1:
                    stat.home_team_score = team_value
                else:
                    stat.away_team_score = team_value
            elif "srb-ParticipantLabel" in clazz:
                labels.append(group.text)
            elif home_team and "srb-ParticipantCenteredStackedMarketRow" in clazz:
                stat = get_stat(labels[table_index])
                stat.home_team_score = odds
                stat.total_amount = abs(handicap)

                table_index += 1
            elif not home_team and "srb-ParticipantCenteredStackedMarketRow" in clazz:
                stat = get_stat(labels[table_index])
                stat.away_team_score = odds
                stat.total_amount = abs(handicap)
                table_index += 1
            elif "gl-MarketColumnHeader" in clazz and table_index > 0:
                table_index = 0
                home_team = False

    driver.close()

    return GameDetailDto(
        overview=overview_dto,
        winner=list(
            set(stats.get(winner_stat_name, [])).union(set(stats.get(money_line, [])))
        ),
        first_blood=stats.get(first_blood_stat_name, []),
        first_kill_baron=stats.get(first_kill_baron_stat_name, []),
        first_destroy_inhibitor=stats.get(first_destroy_inhibitor_stat_name, []),
        total_kills=stats.get(total_kills_stat_name, []),
        total_barons=stats.get(total_barons_stat_name, []),
        total_towers=stats.get(total_towers_stat_name, []),
        tower_handicap=stats.get('tower_handicap', []),
        first_tower=stats.get('first_tower', []),
        kill_handicap=stats.get(kill_handicap_stat_name, []),
        total_dragons=stats.get(total_dragons_stat_name, []),
        first_dragon=stats.get('first_dragon', []),
        total_inhibitors=stats.get(total_inhibitors_stat_name, []),
        game_duration=stats.get(duration_map_stat_name, [])
    )

class Bet365Webscraper(Webscraper):
    @staticmethod
    def create_driver(scraper: Type[Webscraper]) -> webdriver.Chrome:
        return open_url(scraper.get_url())

    @staticmethod
    def get_url() -> str:
        return "https://www.bet365.com/#/AC/B151/C1/D50/E3/F163/"

    def fetch_games(self) -> List[GameDetailDto]:
        league_games = self.driver.find_elements(
            By.CLASS_NAME, "src-CompetitionMarketGroup"
        )
        print(f"[DEBUG] Leagues: {len(league_games)}")
        games: List[GameDetailDto] = []
        league_game_idx = 0
        try:
            while league_game_idx < len(league_games):
                league_game = league_games[league_game_idx]

                league = league_game.find_element(
                    By.CLASS_NAME, "rcl-CompetitionMarketGroupButton"
                ).text
                match_ups = league_game.find_elements(
                    By.CSS_SELECTOR,
                    "div.gl-MarketGroupContainer > div:nth-child(1) > div",
                )
                print(f"[DEBUG]: Matchups: {len(match_ups)}")
                current_match_date = datetime.now()
                match_up_idx = 0
                print(f"[DEBUG] Collecting League: {league}")
                while match_up_idx < len(match_ups):
                    print(
                        f"[DEBUG]: Collecting matchup index: {match_up_idx} / {len(match_ups)}"
                    )
                    match_up = match_ups[match_up_idx]
                    match_up_idx += 1

                    if "rcl-MarketHeaderLabel-isdate" in match_up.get_attribute(
                        "class"
                    ):
                        current_match_date = read_stamp(
                            " ".join(match_up.text.strip().split(" ")[1:])
                        )
                        continue

                    print(f"[DEBUG] Collecting Match")
                    time_string = match_up.find_element(
                        By.CLASS_NAME, "ses-ParticipantFixtureDetailsEsports_Details"
                    ).text
                    print(time_string)
                    try:
                        date = datetime.combine(
                            current_match_date, time_parser.fromisoformat(time_string)
                        )
                    except Exception:
                        print("[DEBUG] Invalid date provided. Skipping...")
                        continue

                    team_elements = match_up.find_elements(
                        By.CSS_SELECTOR,
                        ".ses-ParticipantFixture"
                        "DetailsEsports_TeamAndScores"
                        "Container > div > div",
                    )

                    home_team = team_elements[0].text
                    away_team = team_elements[1].text
                    overview_dto = GameOverviewDto(
                        date, self.driver.current_url, league, home_team, away_team
                    )

                    click_element(self.driver, match_up)
                    url = self.driver.current_url

                    self.driver.close()
                    time.sleep(browser_redirect_wait)

                    games.append(create_detail_dto(url, overview_dto))

                    # Tricking bet365
                    time.sleep(browser_redirect_wait)
                    self.driver = self.create_driver(Bet365Webscraper)
                    self.wait = WebDriverWait(self.driver, 10)

                    time.sleep(browser_redirect_wait)

                    print(f"[DEBUG] Refreshing for stale to prevent stale referencing")
                    league_games = self.driver.find_elements(
                        By.CLASS_NAME, "src-CompetitionMarketGroup"
                    )
                    league_game = league_games[league_game_idx]
                    match_ups = league_game.find_elements(
                        By.CSS_SELECTOR,
                        "div.gl-MarketGroupContainer > div:nth-child(1) > div",
                    )

                league_game_idx += 1
        except Exception as e:
            print(e)
        return games
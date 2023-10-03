import random
import time
from datetime import datetime, date
from typing import Literal, List, Tuple, Union, Dict

from selenium.common import NoSuchElementException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from src.Dtos import GameOverviewDto, GameDetailDto, StatDto
from src.ScrapingService import Webscraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from src.Utils import parse_float, ScrollBox, remove_duplicates

date_format = "%m/%d %H:%M"
max_scroll_height = 2000  # Prevent the scraper from making useless requests by scraping stats for unused values


def xpath_for_team_name(team_type: Literal["Home", "Away"]) -> str:
    return f".//div/div[2]/div[@class='team{team_type}']/div[contains(@class, 'teamName')]/div"


def parse_date(date_text: str, time_text: str) -> date:
    parsed_date = datetime.strptime(f"{date_text} {time_text}", date_format)
    current_year = datetime.now().year
    return parsed_date.replace(year=current_year)


def map_element_to_stat_dto(stat: WebElement) -> Tuple[str, StatDto]:
    home_team_odds = parse_float(stat.find_element(By.CLASS_NAME, "itemTeamAContent_left")
                                 .find_element(By.CLASS_NAME, "odds_value").text)
    away_team_odds = parse_float(stat.find_element(By.CLASS_NAME, "itemTeamBContent_right")
                                 .find_element(By.CLASS_NAME, "odds_value").text)
    result_description = (stat.find_element(By.CLASS_NAME, "itemContent_center")
                          .find_element(By.CLASS_NAME, "resultDescription").text)
    try:
        total_amount = parse_float(stat.find_element(By.CLASS_NAME, "totalAmount_wrap")
                                   .find_element(By.CLASS_NAME, "totalAmount").text)
    except NoSuchElementException:
        total_amount = -1

    return result_description, StatDto(total_amount, home_team_odds, away_team_odds)


class DafabetWebscraper(Webscraper):

    @staticmethod
    def get_url() -> str:
        return "https://esports.e1q1j0ov.com/esport.aspx?LanguageCode=en&token=&merchantScrollOnly=1"

    def fetch_games(self) -> List[GameDetailDto]:
        wait = WebDriverWait(self.driver, 10)
        print("[DEBUG] Navigating to lol games")
        lol_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[text()='LOL']")))
        lol_button.click()

        clear_button = wait.until(EC.element_to_be_clickable((By.XPATH,
                                                              "//div[@class='clear active']/span[text()='Clear']")))
        clear_button.click()

        print("[DEBUG] Cleared items")
        match_items = self.driver.find_elements(By.XPATH,
                                                "//div[@class='matchList']/div")

        detail_dtos = []
        try:
            for item in match_items:
                count = parse_float(item.find_element(By.XPATH, "./div[@class='countOfmatch']").text, 0)
                if count < 1:
                    continue

                print(f"[DEBUG] Starting parsing process for {count} items")
                label_element = item.find_element(By.XPATH, "./label[@class='options_items']")
                label_element.click()

                league = label_element.text
                print(f"[DEBUG] Collecting League: {league}")

                xpath = "//div[@id='scrContainer']/div/div/a"
                elements = self.driver.find_elements(By.XPATH, xpath)[:1]
                for element in elements:
                    dto = self.map_element_to_detail_dto(league, element)
                    if dto is None:
                        continue
                    detail_dtos.append(dto)
                    print(f"[DEBUG] Next game collected")

                label_element.click()
        except Exception as e:
            print(f"Scraper got killed due to {e}. Returning results collected till crash")
        print(f"[DEBUG] Finished scrap with {len(detail_dtos)} elements")
        return detail_dtos

    def get_stats(self, element: WebElement) -> Dict[str, List[StatDto]]:
        stat_elements = self.driver.execute_script("return document.querySelectorAll('.PrematchMarket_eachItem');")
        stats: Dict[str, List[StatDto]] = {}
        for (name, stat) in map(map_element_to_stat_dto, stat_elements):
            if name not in stats:
                stats[name] = []

            stats[name].append(stat)
        return remove_duplicates(stats)

    def map_element_to_detail_dto(self, league, element: WebElement) -> Union[GameDetailDto, None]:
        time.sleep(random.random() * 5 + 1)  # Add some random delay

        overview_dto = self.map_element_to_overview_dto(league, element)
        if overview_dto.game_date <= datetime.now():
            return None

        main_window_handle = self.driver.current_window_handle
        ActionChains(self.driver).key_down(Keys.CONTROL).click(element).key_up(Keys.CONTROL).perform()
        new_tab_handle = None
        for handle in self.driver.window_handles:
            if handle != main_window_handle:
                new_tab_handle = handle
                self.driver.switch_to.window(new_tab_handle)
                break

        wait = WebDriverWait(self.driver, 10)
        game1_button = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[text()='Game 1']"))
        )
        self.driver.execute_script("arguments[0].click();", game1_button)

        stats: Dict[str, List[StatDto]] = (
            ScrollBox(lambda: self.find_element(By.CLASS_NAME, "games_scroll"), max_scroll=max_scroll_height)
            .collect(self.driver, self.get_stats)
        )

        if new_tab_handle:
            self.driver.close()
        self.driver.switch_to.window(main_window_handle)

        return GameDetailDto(
            overview=overview_dto,
            winner=stats.get("Game 1 Win", []),
            first_blood=stats.get("Game 1 First Blood", []),
            first_kill_baron=stats.get("Game 1 First Baron", []),
            first_destroy_inhibitor=stats.get("Game 1 First To Take Inhibitor", []),
            total_kills=stats.get("Game 1 Total Kills", []),
            total_barons=stats.get("Game 1 Total Barons", []),
            total_towers=stats.get("Game 1 Total Turrets Taken", []),
            kill_handicap=stats.get("Game 1 Kills Handicap", []),
            first_dragon=stats.get("Game 1 First Dragon", []),  # Not the total, just to provide a value
            total_inhibitors=stats.get("Game 1 First To Take Inhibitor", [])  # Not the total, just to provide a value
        )

    def map_element_to_overview_dto(self, league: str, element: WebElement) -> GameOverviewDto:
        home_team = element.find_element(By.XPATH, xpath_for_team_name("Home")).text
        away_team = element.find_element(By.XPATH, xpath_for_team_name("Away")).text
        date_text = self.extract_text_only(element.find_element(By.CLASS_NAME, "date"))
        time_text = self.extract_text_only(element.find_element(By.CLASS_NAME, "time"))
        return GameOverviewDto(parse_date(date_text, time_text), self.driver.current_url, league, home_team, away_team)

    def extract_text_only(self, element: WebElement) -> str:
        return self.driver.execute_script("return arguments[0].firstChild.nodeValue;", element).strip()

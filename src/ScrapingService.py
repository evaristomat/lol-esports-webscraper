import random
import time
from abc import abstractmethod
from typing import List, Type, Union

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common import InvalidSessionIdException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium_stealth import stealth

from src.Dtos import GameDetailDto

WAIT_TIMEOUT_BETWEEN_QUERIES_SECONDS = 0.5


class Webscraper:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)

    def find_element(self, by: str, value: str):
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def find_elements(self, by: str, value: str):
        return self.wait.until(EC.presence_of_all_elements_located((by, value)))

    @staticmethod
    def timeout(min_timeout: float = 1, max_timeout: float = 2):
        time.sleep(random.random() * (max_timeout - min_timeout) + min_timeout)

    @staticmethod
    def create_driver(scraper: type) -> webdriver.Chrome:
        driver = create_stealth_driver()
        driver.get(scraper.get_url())
        return driver

    @staticmethod
    @abstractmethod
    def get_url() -> str:
        raise Exception("Not implemented")

    @abstractmethod
    def fetch_games(self) -> List[GameDetailDto]:
        """
        Fetches all game overviews dtos
        :return: Possibly returns an empty list, meaning there's something wrong with the
        Wi-Fi speed. Trying it again usually fixes it
        """
        raise Exception("Not implemented")


def create_stealth_options() -> Options:
    ua = UserAgent()
    user_agent = ua.random

    options = Options()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return options


def create_stealth_driver(
    driver: Union[webdriver.Chrome, None] = None
) -> webdriver.Chrome:
    if driver is None:
        driver = webdriver.Chrome(options=create_stealth_options())

    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                      get: () => undefined
                    })
                  """
        },
    )
    return driver


def fetch_games(scraper: Type[Webscraper]):
    driver = scraper.create_driver(scraper)
    driver.implicitly_wait(WAIT_TIMEOUT_BETWEEN_QUERIES_SECONDS)
    print("[DEBUG] Browser started")
    games = scraper(driver).fetch_games()
    print(games)
    try:
        driver.close()
        driver.quit()
    except InvalidSessionIdException:
        print("Failed closing browser due to invalid session id")
    return games

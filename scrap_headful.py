from typing import Type, List
import concurrent.futures

from src.Dtos import GameDetailDto
from src.Json import write_as_json_to_file
from src.ScrapingService import Webscraper, fetch_games
from src.Utils import get_current_folder

from src.scrapers.Bet365 import Bet365Webscraper
import concurrent.futures
from typing import Type, List

from src.Dtos import GameDetailDto
from src.Json import write_as_json_to_file
from src.ScrapingService import Webscraper, fetch_games
from src.Utils import get_current_folder
from src.scrapers.Bet365 import Bet365Webscraper


def scrap(service: Type[Webscraper]) -> List[GameDetailDto]:
    print(f"[INFO] Started scrap for {service.__name__}")
    games = fetch_games(service)
    write_as_json_to_file(
        f"{get_current_folder()}/games_{service.__name__}.json", games
    )
    return games


def main():
    print("[INFO] Starting scraper")

    # Use ThreadPoolExecutor to run the scraping functions concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(scrap, [Bet365Webscraper])


if __name__ == "__main__":
    main()

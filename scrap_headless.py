from typing import Type, List

from src.Dtos import GameDetailDto
from src.Json import write_as_json_to_file
from src.ScrapingService import Webscraper, fetch_games
from src.Utils import get_current_folder
from src.scrapers.Dafabet import DafabetWebscraper
from src.scrapers.Pinnacle import PinnacleWebscraper


def scrap(service: Type[Webscraper]) -> List[GameDetailDto]:
    print(f"[INFO] Started scrap for {service.__name__}")
    games = fetch_games(service)
    print(games)
    write_as_json_to_file(
        f"{get_current_folder()}/games_{service.__name__}.json", games
    )
    return games


def main():
    print("[INFO] Starting scraper")

    # Use ThreadPoolExecutor to run the scraping functions concurrently
    scrap(PinnacleWebscraper)
    scrap(DafabetWebscraper)


if __name__ == "__main__":
    main()

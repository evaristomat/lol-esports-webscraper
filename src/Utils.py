import math
import os
import random
import time
from datetime import datetime
from itertools import chain
from typing import Callable, TypeVar, Dict, List

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.Dtos import GameDetailDto

T = TypeVar("T")


def get_current_folder() -> str:
    current_date = datetime.now()
    year = current_date.strftime('%Y')
    month = current_date.strftime('%m')
    day = current_date.strftime('%Y-%m-%d')
    
    folder_path = f"./data/{year}/{month}/{day}"
    
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def click_element(driver, element):
    while True:
        try:
            element.click()
            break
        except Exception:
            scroll = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "html"))
            )
            driver.execute_script(f"arguments[0].scrollTop += 250;", scroll)


def read_stamp(date_string: str):
    month_map = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Out": 10,
        "Nov": 11,
        "Dec": 12,
    }
    current_year = datetime.now().year
    day, month_abbr = date_string.split()
    month_number = month_map[month_abbr]
    return datetime(current_year, month_number, int(day))


def parse_float(s: str, default_value: float = -1) -> float:
    try:
        return float(s)
    except ValueError:
        return default_value


def flatmap(func, iterable):
    return chain.from_iterable(map(func, iterable))


def remove_duplicates(input_dict: Dict[str, List[T]]) -> Dict[str, List[T]]:
    return {key: list(set(value)) for key, value in input_dict.items()}


def try_get_element_text(driver, by: str, value: str, default: str) -> str:
    try:
        element = driver.find_element(by, value)
        return element.text
    except NoSuchElementException:
        return default


def find_changed_overviews_and_stats(
    list1: List[GameDetailDto], list2: List[GameDetailDto]
):
    changed_overviews = []
    changed_stats = []
    seen_overviews = {}

    list2_hash_dict = {hash(obj): obj for obj in list2}

    for obj1 in list1:
        hash_value = hash(obj1)
        if hash_value in list2_hash_dict:
            obj2 = list2_hash_dict[hash_value]
            if obj1 != obj2:
                if obj1.overview != obj2.overview:
                    changed_overviews.append(obj1)
                else:
                    changed_stats.append(obj1)
        else:
            changed_overviews.append(obj1)
            overview_hash = hash(obj1.overview)
            if overview_hash not in seen_overviews:
                seen_overviews[overview_hash] = obj1

    return changed_overviews, changed_stats


class ScrollBox:
    def __init__(
        self,
        scrollable_element_provider: Callable[[], WebElement],
        scroll_amount: int = 500,
        max_scroll: int = math.inf,
    ):
        self.scrollable_element_provider = scrollable_element_provider
        self.scroll_amount = scroll_amount
        self.max_scroll = max_scroll

    def collect(
        self, driver: webdriver.Chrome, collector: Callable[[WebElement], Dict[str, T]]
    ) -> Dict[str, T]:
        max_height = self.__get_scroll_height__(driver)

        current_scroll = 0
        collected_elements = {}
        while current_scroll < max_height:
            max_height = self.__get_scroll_height__(driver)

            time.sleep(random.random() + 1)
            element = self.scrollable_element_provider()
            collected_elements.update(collector(element))

            current_scroll += self.scroll_amount
            driver.execute_script(
                f"arguments[0].scrollTop = {current_scroll};", element
            )
        return collected_elements

    def __get_scroll_height__(
        self,
        driver: webdriver.Chrome,
    ) -> int:
        return min(
            driver.execute_script(
                "return arguments[0].scrollHeight;", self.scrollable_element_provider()
            ),
            self.max_scroll,
        )

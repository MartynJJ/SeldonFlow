from seldonflow.data_collection import data_collector
from seldonflow.util.logger import LoggingMixin
from seldonflow.util.env import Environment
from seldonflow.api_client.kalshi_client import KalshiClient
from seldonflow.util import ticker_mapper
from seldonflow.util import custom_methods, custom_types
from seldonflow.data_collection import kalshi_order_book_utils
from seldonflow.util import tick_manager, ticker_mapper, config


import datetime
from typing import Optional, List, Dict
from pathlib import Path
import pandas as pd
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
import time
import re


INTRADAY_FILE_DIR = Path("src/seldonflow/data/shared/weather/intraday_nws/")
DEV_INTRADAY_FILE_DIR = Path("src/seldonflow/data/shared/DEV/weather/intraday_nws/")


class IntradayNwsCollector(LoggingMixin, data_collector.DataCollector):
    def __init__(self, env: Environment = Environment.PRODUCTION):
        super().__init__()
        self._env = env
        self._save_dir = (
            INTRADAY_FILE_DIR
            if self._env == Environment.PRODUCTION
            else DEV_INTRADAY_FILE_DIR
        )
        self._tick_manager = tick_manager.TickManager(tick_manager.ONE_MINUTE)
        self._enabled = True
        self.logger.info(
            f"Intraday NWS Collector Loaded: {self._env} Tick Interval: {self._tick_manager._tick_interval}"
        )
        self.codes = ["knyc"]

        # self.scrape_data("knyc")

    async def on_tick(self, current_time: custom_types.TimeStamp):
        if self._tick_manager.ready_with_auto_update(current_time=current_time):
            for code in self.codes:
                self.logger.info(f"Scraping Intraday data for {code}")
                try:
                    intraday_data = self.scrape_data(code)
                    self.save_data(intraday_data)
                except Exception as e:
                    self.logger.error(f"Error scraping data for {code}: {e}")
        self._tick_manager.align_to_time_point(
            current_time,
            [
                custom_types.Minutes(1),
                custom_types.Minutes(11),
                custom_types.Minutes(21),
                custom_types.Minutes(31),
                custom_types.Minutes(41),
                custom_types.Minutes(51),
            ],
        )

    def collect_station_data(self, station: str) -> Optional[custom_types.Temp]:
        return None

    def get_temp_table(self, site_code: str) -> Optional[WebElement]:

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=800,600")
        MAX_ATTEMPTS = 3
        table: Optional[WebElement] = None
        driver = webdriver.Chrome(options=options)
        url = f"https://www.weather.gov/wrh/timeseries?site={site_code}"
        self.logger.info(f"Loading: {url}")
        driver.get(url)
        for attempt in range(MAX_ATTEMPTS):
            self.logger.info(
                f"Checking for table. Attenpt {attempt+1} / {MAX_ATTEMPTS}"
            )
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, "#OBS_DATA tr")) > 5
                )
                table = driver.find_element(By.ID, "OBS_DATA")
                self.logger.debug("Found table with ID 'OBS_DATA'")
                return table
            except:
                self.logger.info("Could not find table with ID 'OBS_DATA', retrying")

    @staticmethod
    def get_headers_from_rows(rows: List[WebElement]) -> Dict[str, int]:
        headers: Dict[str, int] = dict()
        header_row = rows[0]
        header_cells = header_row.find_elements(By.TAG_NAME, "th")
        if len(header_cells) < 2:
            return {}
        for i, th in enumerate(header_cells):
            header_text = th.get_attribute("innerHTML") or th.text
            header_text = re.sub(r"<[^>]+>", " ", header_text)
            header_text = re.sub(r"\s+", " ", header_text.strip()).replace("&nbsp;", "")

            headers[header_text] = i
        return headers

    def save_data(self, data_frame: pd.DataFrame):
        file_name = self.get_file_name_from_df(data_frame)
        file_path = self._save_dir / file_name
        data_frame.to_csv(file_path)
        return None

    def get_file_name_from_df(self, data_frame: pd.DataFrame):
        datetime_str = data_frame.iloc[0, 0].strftime("%Y%m%d_%H%M%S")
        return f"nws_intraday_{datetime_str}.csv"

    @staticmethod
    def get_header_map(header_dict: Dict[str, int]) -> Dict[str, int]:
        EXPECTED_COL_TO_HEADER = {
            "datetime": 0,
            "temp": 1,
            "6 Hr Max (°F)": -4,
            "6 Hr Min (°F)": -3,
            "24 Hr Max (°F)": -2,
            "24 Hr Min (°F)": -1,
        }
        header_to_col = {
            "datetime": header_dict.get(
                "Date/Time  (L)", EXPECTED_COL_TO_HEADER["datetime"]
            ),
            "temp": header_dict.get("Temp.  (°F)", EXPECTED_COL_TO_HEADER["temp"]),
            "6 Hr Max (°F)": header_dict.get(
                "6 Hr Max (°F)", EXPECTED_COL_TO_HEADER["6 Hr Max (°F)"]
            ),
            "6 Hr Min (°F)": header_dict.get(
                "6 Hr Min (°F)", EXPECTED_COL_TO_HEADER["6 Hr Min (°F)"]
            ),
            "24 Hr Max (°F)": header_dict.get(
                "24 Hr Max (°F)", EXPECTED_COL_TO_HEADER["24 Hr Max (°F)"]
            ),
            "24 Hr Min (°F)": header_dict.get(
                "24 Hr Min (°F)", EXPECTED_COL_TO_HEADER["24 Hr Min (°F)"]
            ),
        }
        return header_to_col

    def scrape_data(self, site_code: str) -> pd.DataFrame:
        table = self.get_temp_table(site_code)
        if table == None:
            return pd.DataFrame()
        assert table != None
        rows = table.find_elements(By.TAG_NAME, "tr")
        self.logger.debug(f"Processing {len(rows)} rows")
        headers = self.get_headers_from_rows(rows)
        data = []
        col_to_header = self.get_header_map(headers)
        for row_num, row in enumerate(rows[1:], 1):
            cells = row.find_elements(By.TAG_NAME, "td")
            if not cells:
                continue
            if len(cells) != len(headers):
                continue
            row_data = {}
            for col_key, col_index in col_to_header.items():
                if col_index < len(cells):
                    innerHTML = cells[col_index].get_attribute("innerHTML")
                    clean_text = re.sub(r"<[^>]*>", "", innerHTML)
                    clean_text = re.sub(r"&nbsp;", " ", clean_text)
                    clean_text = clean_text.strip()
                    row_data[col_key] = clean_text
            data.append(row_data)
        current_year = datetime.datetime.now().year
        data = pd.DataFrame(data)
        data["datetime"] = data["datetime"].apply(
            lambda x: self.parse_nws_datetime_with_inferred_year(x, current_year)
        )
        return pd.DataFrame(data)

    @staticmethod
    def parse_nws_datetime_with_inferred_year(
        date_str, current_year
    ) -> datetime.datetime:
        dt = pd.to_datetime(date_str, format="%b %d, %I:%M %p")

        parsed_dt = dt.replace(year=current_year)

        if parsed_dt > datetime.datetime.now():
            parsed_dt = parsed_dt.replace(year=current_year - 1)
        return parsed_dt


def main():
    env = Environment.DEVELOPMENT
    collector = IntradayNwsCollector(env=env)
    df = collector.scrape_data("knyc")
    print(df.iloc[0, 0].strftime("%Y%m%d_%H%M%S"))


if __name__ == "__main__":
    main()

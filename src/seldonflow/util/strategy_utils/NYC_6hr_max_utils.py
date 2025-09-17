from seldonflow.util import custom_methods, custom_types

import datetime
from typing import Optional, List, Dict
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
import asyncio
import pandas as pd
from datetime import time as Time
from collections import namedtuple
from dataclasses import dataclass


def _set_options():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=800,600")
    return options


OPTIONS = _set_options()
PRINT_DATE_COL_AND_DEFAULT = ("Date/Time  (L)", 0)
SIX_HOUR_MAX_COL_AND_DEFAULT = ("6 Hr Max (°F)", -4)
PRINT_TEMP_COL_AND_DEFAULT = ("Temp.  (°F)", 1)

code_to_alert_times = {"knyc": [Time(hour=13), Time(hour=14)]}


@dataclass
class SixHourTempInfo:
    print_temp: custom_types.Temp
    six_hour_max_temp: custom_types.Temp


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


def clean_cell(cell: WebElement) -> str:
    innerHTML = cell.get_attribute("innerHTML")
    if innerHTML == None:
        return ""
    clean_text = re.sub(r"<[^>]*>", "", innerHTML)
    clean_text = re.sub(r"&nbsp;", " ", clean_text)
    return clean_text.strip()


def parse_nws_datetime_with_inferred_year(date_str, current_year) -> datetime.datetime:
    dt = pd.to_datetime(date_str, format="%b %d, %I:%M %p")

    parsed_dt = dt.replace(year=current_year)

    if parsed_dt > datetime.datetime.now():
        parsed_dt = parsed_dt.replace(year=current_year - 1)
    return parsed_dt


def check_for_6hr_max(
    row: List[str], col_to_idx: Dict[str, int]
) -> Optional[SixHourTempInfo]:
    six_hour_max_col = col_to_idx.get(SIX_HOUR_MAX_COL_AND_DEFAULT[0])
    if six_hour_max_col == None:
        return None
    if len(row) < six_hour_max_col:
        return None

    six_hour_max_temp = row[six_hour_max_col]
    if six_hour_max_temp == "":
        return None
    try:
        six_hour_max_temp = custom_types.Temp.from_f(
            custom_types.TempF(float(row[six_hour_max_col]))
        )
        print_temp = custom_types.Temp.from_f(
            custom_types.TempF(
                float(
                    row[
                        col_to_idx.get(
                            PRINT_TEMP_COL_AND_DEFAULT[0], PRINT_TEMP_COL_AND_DEFAULT[1]
                        )
                    ]
                )
            )
        )
    except ValueError as value_error:
        return None

    return SixHourTempInfo(
        print_temp=print_temp,
        six_hour_max_temp=six_hour_max_temp,
    )


def aggro_get_latest_print(
    site_code="knyc", current_year=2025
) -> Optional[SixHourTempInfo]:
    driver = webdriver.Chrome(options=OPTIONS)
    url = f"https://www.weather.gov/wrh/timeseries?site={site_code}&hours=2"
    driver.get(url)
    WebDriverWait(driver, 3).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "#OBS_DATA tr")) > 1
    )
    table = driver.find_element(By.ID, "OBS_DATA")
    rows = table.find_elements(By.TAG_NAME, "tr")
    headers = get_headers_from_rows(rows)
    if len(rows) < 2:
        raise ValueError("No data rows found in the table")
    top_row = rows[1]
    data = [clean_cell(cell) for cell in top_row.find_elements(By.TAG_NAME, "td")]
    latest_print_time = parse_nws_datetime_with_inferred_year(
        data[headers.get(PRINT_DATE_COL_AND_DEFAULT[0], PRINT_DATE_COL_AND_DEFAULT[1])],
        current_year,
    )
    latest_print_hour = latest_print_time.hour
    for alert_time in code_to_alert_times.get(site_code.lower(), []):
        if alert_time.hour == latest_print_hour:
            return check_for_6hr_max(data, headers)
    return None

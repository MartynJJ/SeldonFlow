from seldonflow.util import custom_types
from seldonflow.util.logger import LoggingMixin
from seldonflow.data_collection import data_collector
from seldonflow.util.tick_manager import TickManager, FIVE_MINUTES
from seldonflow.util import ticker_mapper
from seldonflow.util.env import Environment

import requests
from typing import Optional
import re
from pathlib import Path
from datetime import date as Date
from datetime import datetime
import io
import csv
import os
import pytz

STATION_IDS = ["KNYC", "KJFK", "KLGA", "KEWR"]

DATA_PATH = Path("src/seldonflow/data/shared/weather/metar")
DEV_DATA_PATH = Path("src/seldonflow/data/shared/DEV/weather/metar")

TEMP_LOCATION_TO_STATION = {
    ticker_mapper.TempLocation.NYC: "KNYC",
    ticker_mapper.TempLocation.JFK: "KJFK",
    ticker_mapper.TempLocation.LGA: "KLGA",
    ticker_mapper.TempLocation.EWR: "KEWR",
}


def get_metar_url(station_id: str):
    return (
        f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{station_id}.TXT"
    )


def get_data_filename(
    station: str, date: Date, env: Environment = Environment.PRODUCTION
):
    if env == Environment.PRODUCTION:
        return DATA_PATH / f"{station}_{date.strftime('%Y-%m-%d')}.csv"
    else:
        return DEV_DATA_PATH / f"{station}_{date.strftime('%Y-%m-%d')}.csv"


def format_csv_row(timestamp: custom_types.TimeStamp, temp: custom_types.Temp):
    return [
        timestamp,
        custom_types.time_stamp_to_NYC_str(timestamp),
        f"{temp.as_celsius():.1f}",
        f"{temp.as_fahrenheit():.1f}",
    ]


class MetarCollector(LoggingMixin, data_collector.DataCollector):
    def __init__(self, env: Environment = Environment.PRODUCTION):
        super().__init__()
        self._env = env
        self._ticker_manager = TickManager(custom_types.TimeStamp(FIVE_MINUTES))
        self._stations = STATION_IDS
        self.logger.info(
            f"Meta Data Collector Initialized: {self._env} - Stations: {self._stations}"
        )

    def collect_all_data(self, time_stamp: custom_types.TimeStamp):
        for station in self._stations:
            self.logger.info(f"Collecting metar data for {station}")
            temp = self.collect_station_data(station)
            if temp:
                self.save_data(time_stamp, station, temp)
                self.logger.info(f"Data Saved for {station} = Current Temp: {temp}")

    def collect_station_data(self, station: str) -> Optional[custom_types.Temp]:
        url = get_metar_url(station_id=station)
        response = requests.get(url)
        if response.status_code != 200:
            self.logger.warning(
                f"Metar Request Failed with status code: {response.status_code}"
            )
            return None
        re_find = re.findall(r"T([0-9]{5})", response.text)
        if len(re_find) != 1:
            self.logger.warning(f"Metar Response Unexpected: {response.text}")
            return None
        temp_raw = re_find[0]
        if len(temp_raw) != 5:
            self.logger.warning(
                f"Metar Response Unexpected: {response.text} Temp Exctracted: {temp_raw}"
            )
            return None
        celcius = custom_types.TempC(float(temp_raw[:3] + "." + temp_raw[-2:]))
        return custom_types.Temp(celcius)

    def save_data(
        self, time_stamp: custom_types.TimeStamp, station: str, temp: custom_types.Temp
    ):
        row_formatted = format_csv_row(time_stamp, temp)
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        date = custom_types.time_stamp_to_NYC(time_stamp=time_stamp).date()
        file_name = get_data_filename(station=station, date=date, env=self._env)
        existing_content = os.path.exists(file_name)
        COLUMNS = ["TimeStamp", "Time", "TempC", "TempF"]
        try:
            with open(file_name, "r") as f:
                existing_content = f.read()
                output.write(existing_content.rstrip("\n"))
                if existing_content:
                    output.write("\n")  # Add newline before appending
                writer.writerow(row_formatted)
        except FileNotFoundError:
            # Write header for new file
            self.logger.info(f"Generating new file {file_name}")
            writer.writerow(COLUMNS)
            writer.writerow(row_formatted)
        except NameError:  # Pyodide environment (no file I/O)
            print("C")
            writer.writerow(COLUMNS)
            writer.writerow(row_formatted)
        with open(file_name, "a" if existing_content else "w") as f:
            writer = csv.writer(f, lineterminator="\n")
            if not existing_content:
                writer.writerow(COLUMNS)
            writer.writerow(row_formatted)
        return output.getvalue()

    def on_tick(self, current_time: custom_types.TimeStamp):
        if not self._ticker_manager.ready_with_auto_update(current_time):
            return
        else:
            self.collect_all_data(current_time)

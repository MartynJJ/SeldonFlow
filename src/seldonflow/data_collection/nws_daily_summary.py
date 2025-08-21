from seldonflow.util.env import Environment
from seldonflow.util.logger import LoggingMixin
from seldonflow.util import tick_manager
from seldonflow.util import custom_methods, custom_types
from seldonflow.data_collection import data_collector

import pandas as pd
import requests
import re
from datetime import datetime, date, timedelta
from datetime import time as Time
import pandas as pd
from pathlib import Path
from typing import Optional, Set

MAX_NWS_VERSION = 50

NWS_SUMMARY_OUTPUT_PATH = Path("src/seldonflow/data/shared/weather/scraped")
DEV_NWS_SUMMARY_OUTPUT_PATH = Path("src/seldonflow/data/shared/DEV/weather/scraped")

NWS_DAILY_SUMMARY_OUTPUT_PATH = Path("src/seldonflow/data/shared/weather/nws_ds")
DEV_NWS_DAILY_SUMMARY_OUTPUT_PATH = Path(
    "src/seldonflow/data/shared/DEV/weather/nws_ds"
)


def scrape_nws_climate(version=1):
    url = f"https://forecast.weather.gov/product.php?site=OKX&issuedby=NYC&product=CLI&format=TXT&version={version}&glossary=0"
    try:
        response = requests.get(url)
        response.raise_for_status()
        text = response.text

        data = {
            "STATION": "CLINYC",  # Station identifier (e.g., CLINYC for Central Park, NY)
            "NAME": "Central Park NY",  # Name of the weather station location
            "DATE": None,  # Observation date (YYYY-MM-DD, typically the day before the release date)
            "RELEASE_DATE": None,  # Issuance date of the report (YYYY-MM-DD, e.g., date the report was published)
            "TIME": None,  # Issuance time of the report (HH:MM in 24-hour format, e.g., 02:17)
            "AWND": None,  # Average daily wind speed (mph, two-minute sustained wind)
            "PGTM": None,  # Time of peak wind gust (HHMM in 24-hour format, e.g., 1500 for 3:00 PM)
            "PRCP": None,  # Daily precipitation (inches, total for the day; T for trace amounts)
            "SNOW": None,  # Daily snowfall (inches; T for trace amounts)
            "SNWD": None,  # Snow depth at observation time (inches; T for trace amounts)
            "TAVG": None,  # Average daily temperature (degrees Fahrenheit, mean of TMAX and TMIN)
            "TMAX": None,  # Maximum daily temperature (degrees Fahrenheit)
            "TMIN": None,  # Minimum daily temperature (degrees Fahrenheit)
            "WDF2": None,  # Direction of highest wind speed (degrees, e.g., 220 for SW)
            "WDF5": None,  # Direction of highest wind gust (degrees, e.g., 240 for SW)
            "WSF2": None,  # Highest wind speed (mph, two-minute sustained wind)
            "WSF5": None,  # Highest wind gust speed (mph)
            "WT01": 0,  # Fog indicator (1 if fog observed, 0 otherwise)
            "WT02": 0,  # Heavy fog indicator (1 if heavy fog observed, 0 otherwise)
            "WT03": 0,  # Thunder indicator (1 if thunder observed, 0 otherwise)
            "WT06": 0,  # Rain or shower indicator (1 if rain or showers observed, 0 otherwise)
            "WT08": 0,  # Haze indicator (1 if haze observed, 0 otherwise)
        }

        issuance_match = re.search(
            r"(\d{1,2}:?\d{0,2}\s+(?:AM|PM))\s+EDT\s+\w+\s+(\w+\s+\d{1,2}\s+\d{4})",
            text,
        )
        if issuance_match:
            time_str = issuance_match.group(1)
            release_date_str = issuance_match.group(2)
            # Handle both "2:17 AM" and "217 AM" formats for time
            time_str = (
                re.sub(r"(\d{1,2})(\d{2})\s+(AM|PM)", r"\1:\2 \3", time_str)
                if ":" not in time_str
                else time_str
            )
            time_dt = datetime.strptime(time_str, "%I:%M %p")
            data["TIME"] = time_dt.strftime("%H:%M")
            # Parse and format release date
            release_date_dt = datetime.strptime(release_date_str, "%b %d %Y")
            data["RELEASE_DATE"] = release_date_dt.strftime("%Y-%m-%d")

        # observation date (e.g., "JULY 18 2025")
        date_match = re.search(r"CLIMATE SUMMARY FOR (\w+ \d{1,2} \d{4})", text)
        if date_match:
            date_str = date_match.group(1)
            data["DATE"] = datetime.strptime(date_str, "%B %d %Y").strftime("%Y-%m-%d")

        # temperature data
        tmax_match = re.search(r"MAXIMUM\s+(\d+)\s+\d{1,2}:?\d*\s+(?:AM|PM)", text)
        tmin_match = re.search(r"MINIMUM\s+(\d+)\s+\d{1,2}:?\d*\s+(?:AM|PM)", text)
        tavg_match = re.search(r"AVERAGE\s+(\d+)", text)
        if tmax_match:
            data["TMAX"] = int(tmax_match.group(1))
        if tmin_match:
            data["TMIN"] = int(tmin_match.group(1))
        if tavg_match:
            data["TAVG"] = int(tavg_match.group(1))

        # precipitation
        prcp_match = re.search(r"PRECIPITATION \(IN\)\s+YESTERDAY\s+(\d+\.\d+|T)", text)
        if prcp_match:
            data["PRCP"] = (
                0.0 if prcp_match.group(1) == "T" else float(prcp_match.group(1))
            )

        # snowfall and snow depth
        snow_match = re.search(r"SNOWFALL \(IN\)\s+YESTERDAY\s+(\d+\.\d+|T)", text)
        snwd_match = re.search(r"SNOW DEPTH\s+(\d+|T)", text)
        if snow_match:
            data["SNOW"] = (
                0.0 if snow_match.group(1) == "T" else float(snow_match.group(1))
            )
        if snwd_match:
            data["SNWD"] = (
                0.0 if snwd_match.group(1) == "T" else float(snwd_match.group(1))
            )

        # wind data
        awnd_match = re.search(r"AVERAGE WIND SPEED\s+(\d+\.\d+)", text)
        wsf2_match = re.search(r"HIGHEST WIND SPEED\s+(\d+)", text)
        wdf2_match = re.search(r"HIGHEST WIND DIRECTION\s+\w+\s+\((\d+)\)", text)
        wsf5_match = re.search(r"HIGHEST GUST SPEED\s+(\d+)", text)
        wdf5_match = re.search(r"HIGHEST GUST DIRECTION\s+\w+\s+\((\d+)\)", text)
        if awnd_match:
            data["AWND"] = float(awnd_match.group(1))
        if wsf2_match:
            data["WSF2"] = int(wsf2_match.group(1))
        if wdf2_match:
            data["WDF2"] = int(wdf2_match.group(1))
        if wsf5_match:
            data["WSF5"] = int(wsf5_match.group(1))
        if wdf5_match:
            data["WDF5"] = int(wdf5_match.group(1))

        # peak gust time (PGTM)
        pgtm_match = re.search(
            r"HIGHEST GUST SPEED\s+\d+\s+HIGHEST GUST DIRECTION\s+\w+\s+\(\d+\)\s+(\d{1,2}:?\d*\s+(?:AM|PM))",
            text,
        )
        if pgtm_match:
            time_str = pgtm_match.group(1)
            # Handle both "5:34 PM" and "534 PM" formats
            time_str = re.sub(
                r"(\d{1,2})(\d{2})\s+(AM|PM)", r"\1:\2 \3", time_str
            )  # Add colon if missing
            pgtm_dt = datetime.strptime(time_str, "%I:%M %p")
            data["PGTM"] = pgtm_dt.strftime("%H%M")

        # weather conditions
        weather_conditions = re.search(
            r"WEATHER CONDITIONS\s+THE FOLLOWING WEATHER WAS RECORDED YESTERDAY\.\s+(.+?)\s+\.",
            text,
            re.DOTALL,
        )
        if weather_conditions:
            conditions = weather_conditions.group(1).lower()
            if "fog" in conditions:
                data["WT01"] = 1
            if "heavy fog" in conditions:
                data["WT02"] = 1
            if "thunder" in conditions:
                data["WT03"] = 1
            if "rain" in conditions or "shower" in conditions:
                data["WT06"] = 1
            if "haze" in conditions:
                data["WT08"] = 1
        else:
            # If "NO SIGNIFICANT WEATHER" is present, keep weather types as 0
            if "NO SIGNIFICANT WEATHER" in text:
                pass

        return data

    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        print(f"Error parsing data: {e}")
        return None


class DailySummaryCollector(LoggingMixin, data_collector.DataCollector):
    def __init__(
        self,
        env: Environment,
        scrape_date: Optional[date] = None,
    ):
        super().__init__()
        self._env = env
        self._tick_manager = tick_manager.TickManager(
            tick_interval=tick_manager.FIVE_MINUTES
        )
        self._output_path = (
            NWS_SUMMARY_OUTPUT_PATH
            if self._env == Environment.PRODUCTION
            else DEV_NWS_SUMMARY_OUTPUT_PATH
        )
        self._nws_ds_path = (
            NWS_DAILY_SUMMARY_OUTPUT_PATH
            if self._env == Environment.PRODUCTION
            else DEV_NWS_DAILY_SUMMARY_OUTPUT_PATH
        )
        self._date = scrape_date or datetime.today().date()
        self._output_filename = f"NWS_SCRAPE_{self._date.isoformat()}.csv"
        self._data: Optional[pd.DataFrame] = None
        self._events = {
            Time(hour=3): {
                "run_next_day_offical_task",
            },
            Time(hour=16): {
                "run_same_day_inital_task",
            },
        }
        self._events_in_queue: Set[str] = set()
        self._completed_daily_tasks: Set[str] = set()
        self.logger.info(
            f"DailySummaryCollector initliazed: {self._env} - {self._events}"
        )

    def collect_station_data(self, station: str) -> Optional[custom_types.Temp]:
        pass

    def on_tick(self, current_time: custom_types.TimeStamp):
        if self._tick_manager.ready_with_auto_update(current_time=current_time):
            self.time_event_handler(current_time=current_time)

    def time_event_handler(self, current_time: custom_types.TimeStamp):
        nyc_time = custom_methods.time_stamp_to_NYC(current_time)
        nyc_hour = Time(hour=nyc_time.hour)
        events_to_process = self._events.get(nyc_hour)
        all_events_to_process = (
            self._events_in_queue.union(events_to_process)
            if events_to_process
            else self._events_in_queue
        )
        if len(all_events_to_process) > 0:
            self.logger.info(f"Found {len(all_events_to_process)} event(s) to process")
            for event in list(all_events_to_process):
                if event not in self._completed_daily_tasks:
                    self.logger.info(f"Processing task: {event} for {nyc_time}")
                    self._events_in_queue.add(event)
                    task = getattr(self, event)
                    success = task(current_time)
                    if success:
                        self._completed_daily_tasks.add(event)
                        self._events_in_queue.remove(event)
                    else:
                        self.logger.info(
                            f"Event: {event} unsuccessful. Events still in queue for next run {self._events_in_queue}"
                        )

    def run_next_day_offical_task(self, current_time: custom_types.TimeStamp) -> bool:
        data = self.pull_next_day_offical(current_time=current_time)
        if not custom_methods.is_valid_dataframe(data):
            self.logger.info(f"run_next_day_offical_task not completed")
            return False
        assert type(data) == pd.DataFrame
        try:
            data_date = date.fromisoformat(str(data.loc[1, "DATE"]))
            self.save_next_day_official(data_date=data_date, data=data)
            return True
        except Exception as e:
            self.logger.warning(f"NWS Daily Summary Offical Failed: {e}")
            return False

    def save_next_day_official(self, data_date: date, data: pd.DataFrame):
        file_path = (
            self._nws_ds_path / f"nws_offical_ds_{data_date.strftime('%Y%m%d')}.csv"
        )
        data.to_csv(file_path)

    def run_same_day_inital_task(self, current_time: custom_types.TimeStamp) -> bool:
        data = self.pull_same_day_initial(current_time=current_time)
        if not custom_methods.is_valid_dataframe(data):
            self.logger.info(f"run_same_day_inital_task not completed")
            return False
        assert type(data) == pd.DataFrame
        try:
            data_date = date.fromisoformat(str(data.loc[1, "DATE"]))
            self.save_same_day_initial(data_date=data_date, data=data)
            return True
        except Exception as e:
            self.logger.warning(f"NWS Daily Summary Initial Failed: {e}")
            return False

    def save_same_day_initial(self, data_date: date, data: pd.DataFrame):
        file_path = (
            self._nws_ds_path / f"nws_initial_ds_{data_date.strftime('%Y%m%d')}.csv"
        )
        data.to_csv(file_path)

    def pull_same_day_initial(
        self, current_time: custom_types.TimeStamp
    ) -> Optional[pd.DataFrame]:
        data = self.get_version_data(version=1)
        today = custom_methods.time_stamp_to_NYC(current_time).date()
        if not custom_methods.is_valid_dataframe(data):
            self.logger.warning(
                f"DataMissing for initial same day release. Today = {today}"
            )
            return None
        assert type(data) == pd.DataFrame
        if not len(data) == 1:
            self.logger.warning(
                f"Too many rows received in single data pull: {data.shape}"
            )
        data_release_date = date.fromisoformat(str(data.loc[1, "RELEASE_DATE"]))
        data_date = date.fromisoformat(str(data.loc[1, "DATE"]))
        if data_release_date != today or (data_date != today):
            self.logger.info(
                f"Initial Same Day Data Not Avaliable DataDate = {data_date}, DataReleaseDate = {data_release_date}, Today = {today}"
            )
            return None
        self.logger.info(
            f"Successfully pulled inital NWS Daily Summary for {data_date}"
        )
        return data

    def pull_next_day_offical(
        self, current_time: custom_types.TimeStamp
    ) -> Optional[pd.DataFrame]:
        data = self.get_version_data(version=1)
        today = custom_methods.time_stamp_to_NYC(current_time).date()
        yesterday = today - timedelta(days=1)
        if not custom_methods.is_valid_dataframe(data):
            self.logger.warning(
                f"DataMissing for offical next day release. Today = {today}"
            )
            return None
        assert type(data) == pd.DataFrame
        if not len(data) == 1:
            self.logger.warning(
                f"Too many rows received in single data pull: {data.shape}"
            )
        data_release_date = date.fromisoformat(str(data.loc[1, "RELEASE_DATE"]))
        data_date = date.fromisoformat(str(data.loc[1, "DATE"]))
        if data_release_date != today or (data_date != yesterday):
            self.logger.info(
                f"Offical Next Day Data Not Avaliable DataDate = {data_date}, DataReleaseDate = {data_release_date}, Today = {today}"
            )
            return None
        return data

    def get_data(self, max_version=MAX_NWS_VERSION) -> pd.DataFrame:
        data_frames = []
        for version in range(1, max_version + 1):
            try:
                df = self.get_version_data(version=version)
                if custom_methods.is_valid_dataframe(df):
                    data_frames.append(df)
            except Exception as e:
                self.logger.warning(f"Failed to scrape version {version}: {e}")
        if data_frames:
            return pd.concat(data_frames)
        else:
            raise RuntimeError("No data was scraped.")

    def get_version_data(self, version: int) -> Optional[pd.DataFrame]:
        try:
            data = scrape_nws_climate(version=version)
            df = pd.DataFrame(data, index=[version])
            return df
        except Exception as e:
            raise ValueError(f"Failed to scrape version {version}: {e}")

    def save_data(self, data: pd.DataFrame) -> None:
        self._output_path.mkdir(parents=True, exist_ok=True)
        file_path = self._output_path / self._output_filename
        try:
            data.to_csv(file_path)
            self.logger.info(f"Data saved to {file_path}")
        except Exception as e:
            self.logger.info(f"Error saving data: {e}")

    def run_most_recent(self):
        single_run = self.get_version_data(1)
        return single_run

    def run_full(self) -> None:
        self._data = self.get_data()
        self.save_data(self._data)


def main() -> None:
    weather_scaper = DailySummaryCollector(Environment.DEVELOPMENT)
    # weather_scaper.run()
    # if weather_scaper._data is not None and not weather_scaper._data.empty:
    #     first_row = weather_scaper._data.iloc[0]
    #     print(
    #         f"Last Data: TMAX: {first_row.get('TMAX', 'N/A')} TMIN: {first_row.get('TMIN', 'N/A')}"
    #     )
    # else:
    #     print("Last Data: No data to display.")
    now = custom_types.TimeStamp(datetime.now().timestamp())
    data = weather_scaper.pull_next_day_offical(now)
    weather_scaper.time_event_handler(now)
    # print(data)


if __name__ == "__main__":
    main()

from seldonflow.util import custom_types, custom_methods
from seldonflow.util.logger import LoggingMixin
from seldonflow.data_collection import data_collector
from seldonflow.util.env import Environment
from seldonflow.util import tick_manager
from seldonflow.util import ticker_mapper

import requests
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import date as Date
from datetime import time as Time
from datetime import datetime
import pandas as pd

DATA_PATH = Path("src/seldonflow/data/shared/weather/nws_forecast")
DEV_DATA_PATH = Path("src/seldonflow/data/shared/DEV/weather/nws_forecast")

NWS_FORECAST_HEADER = {
    "User-Agent": "(Martyn Jepson, martyn@jepson.dev)",
}  # TODO: move to config

TEMP_LOCATION_TO_NWS_URL = {
    ticker_mapper.TempLocation.NYC: "https://api.weather.gov/gridpoints/OKX/34,38/forecast/hourly",
}

LOCATIONS_IN_USE = [ticker_mapper.TempLocation.NYC]

CALL_TIMES_NY = {Time(hour=4), Time(hour=8), Time(hour=15), Time(hour=22)}


def get_news_forecast_filepath(
    data_path: Path, location: ticker_mapper.TempLocation, hour: int, date: Date
):
    return f"{data_path}/NWS_FORECAST_{date.strftime('%Y%m%d')}_{location.value}_{Time(hour=hour).strftime('%H%M')}.csv"


class NwsForecastCollector(LoggingMixin, data_collector.DataCollector):
    def __init__(self, env: Environment = Environment.PRODUCTION):
        super().__init__()
        self._env = env
        self._ticker_manager = tick_manager.TickManager(
            custom_types.TimeStamp(tick_manager.FIVE_MINUTES)
        )
        self._stations = LOCATIONS_IN_USE

        self._call_times_collected = set()
        self._call_times_requred = CALL_TIMES_NY
        self._data_path = (
            DATA_PATH if self._env == Environment.PRODUCTION else DEV_DATA_PATH
        )

        self.logger.info(
            f"NWS Forecast Collector Initialized: {self._env} - Stations: {self._stations}"
        )
        self._today = Date.fromisoformat("1900-01-01")

    def new_day(self):
        self._call_times_collected.clear()

    def on_tick(self, current_time: custom_types.TimeStamp):
        if not self._ticker_manager.ready_with_auto_update(current_time):
            return
        nyc_time = custom_methods.time_stamp_to_NYC(current_time)
        nyc_date = nyc_time.date()
        if nyc_date != self._today:
            self.new_day()
        self._today = nyc_date
        nyc_hour = nyc_time.hour
        if self.is_call_time_required(
            hour=nyc_hour
        ) and not self.is_call_time_collected(hour=nyc_hour):
            for location in self._stations:
                self.pull_and_save_forecast(nyc_hour, location)

    def pull_and_save_forecast(self, hour: int, location: ticker_mapper.TempLocation):
        self.logger.info(
            f"Pulling NWS Forecast for {location} - {Time(hour=hour).strftime('%H:%M')}"
        )
        response_opt = self.get_forecast_hourly(location=location)
        if not response_opt:
            self.logger.warning(
                f"NWS Data Pull Failed Location: {location.value} hour: {hour}"
            )
            return
        else:
            assert response_opt
            parsed_forecast_list = self.parse_response_data(response_opt)
            if not parsed_forecast_list or len(parsed_forecast_list) == 0:
                self.logger.warning(f"NWS Data Pull Failed")
                return None
            df = pd.DataFrame(parsed_forecast_list)
            df["temp_F"] = df["temp"].apply(lambda x: x.as_fahrenheit() if x else None)
            df["temp_C"] = df["temp"].apply(lambda x: x.as_celsius() if x else None)
            df = df.drop("temp", axis=1)
            filepath = get_news_forecast_filepath(
                data_path=self._data_path,
                location=location,
                hour=hour,
                date=self._today,
            )
            df.to_csv(
                filepath,
                index=False,
            )
            self._call_times_collected.add(hour)
            self.logger.info(f"NWS Forecast Saved: {filepath}")

    def is_call_time_collected(self, hour: int):
        return hour in self._call_times_collected

    def is_call_time_required(self, hour: int):
        hour_time = Time(hour=hour)
        return hour_time in self._call_times_requred

    def get_forecast_hourly(self, location: ticker_mapper.TempLocation):
        url = TEMP_LOCATION_TO_NWS_URL[location]
        response = requests.get(url, headers=NWS_FORECAST_HEADER)
        if response.status_code != 200:
            self.logger.warning(
                f"NWS Data Pull Failed with Status Code {response.status_code}"
            )
            return None
        else:
            return response.json()

    def parse_forecast_period(self, forecast_period: Dict[str, Any]) -> Dict[str, Any]:
        start_time = forecast_period.get("startTime")
        end_time = forecast_period.get("endTime")
        unit = forecast_period.get("temperatureUnit")
        temp_raw = forecast_period.get("temperature")
        if (not start_time) or (not end_time) or (not temp_raw) or (unit != "F"):
            return {
                "start_time_parsed": None,
                "end_time_parsed": None,
                "temp": None,
                "probabilityOfPrecipitation": None,
                "dew_point": None,
                "wind_speed_mph": None,
                "wind_direction": None,
                "relative_humidity": None,
            }
        start_time_parsed = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_time_parsed = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        temp_parsed = custom_types.Temp.from_f(custom_types.TempF(temp_raw))
        probability_of_precipitation = forecast_period.get(
            "probabilityOfPrecipitation", {}
        ).get("value")
        dew_point = forecast_period.get("dewpoint", {}).get("value")
        wind_speed_raw = forecast_period.get("windSpeed")
        if not wind_speed_raw or wind_speed_raw[-4:] != " mph":
            wind_speed_mph = None
        else:
            wind_speed_mph = wind_speed_raw[:-4]
        wind_direction_opt = forecast_period.get("windDirection")
        wind_direction = (
            custom_methods.get_degress_from_direction(wind_direction_opt)
            if wind_direction_opt
            else None
        )
        relative_humidity = forecast_period.get("relativeHumidity", {}).get("value")
        return {
            "start_time_parsed": start_time_parsed,
            "end_time_parsed": end_time_parsed,
            "temp": temp_parsed,
            "probabilityOfPrecipitation": probability_of_precipitation,
            "dew_point": dew_point,
            "wind_speed_mph": wind_speed_mph,
            "wind_direction": wind_direction,
            "relative_humidity": relative_humidity,
        }

    def parse_response_data(
        self, response_data: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        properties = response_data.get("properties")
        if not properties:
            self.logger.warning(f"Missing Properties from NWS Data")
            return None
        periods_opt = properties.get("periods")
        if not periods_opt:
            self.logger.warning(f"Missing Periods from NWS Data")
            return None
        else:
            return [self.parse_forecast_period(period) for period in periods_opt]

    def collect_station_data(self, station: str) -> Optional[custom_types.Temp]:
        return None

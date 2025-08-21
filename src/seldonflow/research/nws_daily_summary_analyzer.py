from seldonflow.util.logger import LoggingMixin
from seldonflow.util.env import Environment

import os
from pathlib import Path
from datetime import date as Date
import pandas as pd
from typing import Dict, Any

NWS_SUMMARY_DIR = Path("src/seldonflow/data/shared/weather/scraped")
NWS_SUMMARY_TMAX_PATH = Path("src/seldonflow/data/shared/weather/nws_ds/")
DEV_NWS_SUMMARY_TMAX_PATH = Path("src/seldonflow/data/shared/DEV/weather/nws_ds/")


def get_nws_summary_filename(date: Date):
    return Path(f"NWS_SCRAPE_{date.strftime('%Y-%m-%d')}.csv")


class NWSDailySummaryAnalyzer(LoggingMixin):
    _FILE_NAME = "TMAX_Daily_Summary.csv"

    def __init__(self, env: Environment):
        super().__init__()
        self._env = env
        self._enabled = True
        self._output_path = (
            NWS_SUMMARY_TMAX_PATH
            if self._env == Environment.PRODUCTION
            else DEV_NWS_SUMMARY_TMAX_PATH
        )
        self.check_dir()

    def produce_and_save_summary(self):
        output_df = self.get_nws_final_max_temp()
        file_path = self._output_path / self._FILE_NAME
        self.logger.info(
            f"Saving {file_path} - First Dat: {output_df.iloc[0]} Last Date: {output_df.iloc[-1]}"
        )
        output_df.to_csv(file_path)

    def check_dir(self):
        is_dir = NWS_SUMMARY_DIR.is_dir()
        if not is_dir:
            self.logger.error(f"Incorrect Dir for NWS Summary {NWS_SUMMARY_DIR}")
            self._enabled = False

    def get_all_files(self) -> Dict[Date, pd.DataFrame]:
        files = os.listdir(NWS_SUMMARY_DIR)
        summary_files = {}
        for file in files:
            if self.check_file_name_format(file):
                file_date = Date.fromisoformat(file[11:-4])
                file_path = NWS_SUMMARY_DIR / file
                try:
                    summary_files[file_date] = pd.read_csv(file_path)
                except FileNotFoundError as file_not_found_e:
                    self.logger.error(f"Missing File: {file_not_found_e}")
        return summary_files

    def get_nws_final_max_temp(self):
        output_df = pd.DataFrame(columns=["Date", "MaxTemp"])
        files = self.get_all_files()
        dates = list(files.keys())
        dates.sort()
        for date in dates:
            df = files.get(date, pd.DataFrame())
            assert len(df)
            df["DATE"] = pd.to_datetime(df["DATE"])
            df["RELEASE_DATE"] = pd.to_datetime(df["RELEASE_DATE"])
            new_dates = df.loc[~df["DATE"].isin(output_df["Date"].to_list())].copy()
            new_dates_final_release = new_dates.loc[
                new_dates["DATE"] != new_dates["RELEASE_DATE"]
            ].copy()
            new_dates_final_release.rename(
                columns={
                    "DATE": "Date",
                    "TMAX": "MaxTemp",
                },
                inplace=True,
            )
            output_df = pd.concat(
                [output_df, new_dates_final_release.loc[:, ["Date", "MaxTemp"]]]
            )
        output_df.set_index("Date", inplace=True)
        return output_df

    @staticmethod
    def check_file_name_format(file_name: str):
        prefix_correct = file_name[:11] == "NWS_SCRAPE_"
        postfix_correct = file_name[-4:] == ".csv"
        return prefix_correct and postfix_correct


def main():
    env = Environment.DEVELOPMENT
    summary_analzyer = NWSDailySummaryAnalyzer(env)
    summary_analzyer.produce_and_save_summary()


if __name__ == "__main__":
    main()

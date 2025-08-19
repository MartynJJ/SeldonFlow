from seldonflow.util.logger import LoggingMixin
from seldonflow.util.env import Environment

import os
from pathlib import Path
from datetime import date as Date

NWS_SUMMARY_DIR = Path("src/seldonflow/data/shared/weather/scraped")


def get_nws_summary_filename(date: Date):
    return Path(f"NWS_SCRAPE_{date.strftime('%Y-%m-%d')}.csv")


class NWSDailySummaryAnalyzer(LoggingMixin):
    def __init__(self, env: Environment):
        super().__init__()
        self._env = env
        self._enabled = True
        self.check_dir()

    def check_dir(self):
        is_dir = NWS_SUMMARY_DIR.is_dir()
        if not is_dir:
            self.logger.error(f"Incorrect Dir for NWS Summary {NWS_SUMMARY_DIR}")
            self._enabled = False

    def get_all_files(self):
        files = os.listdir(NWS_SUMMARY_DIR)
        summary_files = []
        for file in files:
            if self.check_file_name_format(file):
                summary_files.append(summary_files)
        return summary_files

    @staticmethod
    def check_file_name_format(file_name: str):
        prefix_correct = file_name[:11] == "NWS_SCRAPE_"
        postfix_correct = file_name[-4:] == ".csv"
        return prefix_correct and postfix_correct


def main():
    env = Environment.DEVELOPMENT
    print(NWS_SUMMARY_DIR.is_dir())
    print(get_nws_summary_filename(Date.fromisoformat("2025-08-17")))
    print(
        (
            NWS_SUMMARY_DIR / get_nws_summary_filename(Date.fromisoformat("2025-08-17"))
        ).is_file()
    )
    summary_analzyer = NWSDailySummaryAnalyzer(env)
    summary_analzyer.get_all_files()


if __name__ == "__main__":
    main()

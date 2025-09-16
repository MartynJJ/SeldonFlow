from seldonflow.util.env import Environment
from seldonflow.util import custom_methods, custom_types

from pathlib import Path
import os
import datetime
import pandas as pd
from typing import Optional, Dict, AnyStr


INTRADAY_FILE_DIR = Path("src/seldonflow/data/shared/weather/intraday_nws/")
DEV_INTRADAY_FILE_DIR = Path("src/seldonflow/data/shared/DEV/weather/intraday_nws/")
ABSOLUTE_ZERO = custom_types.Temp.from_f(custom_types.TempF(-459.67))


def get_latest_file(env: Environment = Environment.PRODUCTION) -> Path:
    file_dir = (
        INTRADAY_FILE_DIR if env == Environment.PRODUCTION else DEV_INTRADAY_FILE_DIR
    )
    files = [
        file
        for file in os.listdir(file_dir)
        if file.startswith("nws_intraday_") and file.endswith(".csv")
    ]
    if len(files) == 0:
        raise FileExistsError
    else:
        return file_dir / Path(
            max(
                files,
                key=lambda x: datetime.datetime.strptime(
                    x, "nws_intraday_%Y%m%d_%H%M%S.csv"
                ),
            )
        )


def get_max_daily_temp(
    df: pd.DataFrame, current_time: custom_types.TimeStamp
) -> Dict[str, custom_types.Temp]:
    current_datetime = custom_methods.time_stamp_to_NYC(current_time)
    current_date = current_datetime.date()
    df.datetime = pd.to_datetime(df.datetime)
    df = (df.loc[df.datetime.apply(lambda x: x.date() == current_date)]).copy()
    max_snapshot = df.temp.max()
    df_6hr = (
        df.loc[
            df.datetime.apply(
                lambda x: (x - datetime.timedelta(hours=6)).date() == current_date
            )
        ]
    ).copy()
    max_6hr = df_6hr["6 Hr Max (°F)"].max()
    return {
        "Snapshot": custom_types.Temp.from_f(max_snapshot),
        "6_hr": custom_types.Temp.from_f(max_6hr),
    }


def main():
    current_time = custom_types.TimeStamp(1758040285.5192103)
    file_path = get_latest_file()
    df = pd.read_csv(file_path)

    print(get_max_daily_temp(df, current_time))


if __name__ == "__main__":
    main()

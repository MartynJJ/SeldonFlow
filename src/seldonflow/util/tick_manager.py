from seldonflow.util import custom_methods, custom_types
from seldonflow.util.logger import LoggingMixin

from typing import List, Optional
from datetime import timedelta
from datetime import time as Time

ONE_MINUTE = custom_types.TimeStamp(60)
FIVE_MINUTES = custom_types.TimeStamp(300)
ONE_HOUR = custom_types.TimeStamp(3600)
THIRTY_SECONDS = custom_types.TimeStamp(30)


class TickManager(LoggingMixin):
    _next_tick_update: custom_types.TimeStamp

    def __init__(
        self,
        tick_interval: custom_types.TimeStamp,
        time_window: Optional[custom_types.TimeWindow] = None,
        name: Optional[str] = None,
    ):
        super().__init__()
        self._name = name if name != None else "NoName"
        self._tick_interval = tick_interval
        self._next_tick_update = custom_types.TimeStamp(0.0)
        self._time_window = time_window

    def ready(self, current_time: custom_types.TimeStamp):
        if current_time < self._next_tick_update:
            return False
        else:
            return self.in_time_window(current_time=current_time)

    def in_time_window(self, current_time: custom_types.TimeStamp) -> bool:
        if self._time_window == None:
            return True
        else:
            as_datetime = custom_methods.time_stamp_to_NYC(current_time)
            as_time = Time(hour=as_datetime.hour, minute=as_datetime.minute)
            if as_time < self._time_window.start_time:
                next_update = as_datetime.replace(
                    hour=self._time_window.start_time.hour,
                    minute=self._time_window.start_time.minute,
                    second=self._time_window.start_time.second,
                    microsecond=self._time_window.start_time.microsecond,
                )
                self._next_tick_update = custom_types.TimeStamp(next_update.timestamp())
                self.logger.info(
                    f"{self._name} before timewindow, next update {next_update}"
                )
                return False
            if as_time > self._time_window.end_time:
                next_day = (as_datetime + timedelta(days=1)).day
                next_update = as_datetime.replace(
                    day=next_day,
                    hour=self._time_window.start_time.hour,
                    minute=self._time_window.start_time.minute,
                    second=self._time_window.start_time.second,
                    microsecond=self._time_window.start_time.microsecond,
                )

                self._next_tick_update = custom_types.TimeStamp(next_update.timestamp())
                self.logger.info(
                    f"{self._name} after timewindow, next update {next_update}"
                )
                return False
            return True

    def update_next_tick(self, current_time: custom_types.TimeStamp):
        self._next_tick_update = custom_types.TimeStamp(
            current_time + self._tick_interval
        )

    def align_to_time_point(
        self,
        current_time: custom_types.TimeStamp,
        time_points: List[custom_types.Minutes],
    ):
        current_datetime = custom_types.time_stamp_to_NYC(current_time)
        current_min = current_datetime.minute
        next_mins = [m for m in time_points if m > current_min]
        if next_mins:
            next_min = min(next_mins)
            delta = next_min - current_min
        else:

            next_min = min(time_points)
            delta = (60 - current_min) + next_min

        new_dt = current_datetime.replace(second=0, microsecond=0) + timedelta(
            minutes=delta
        )

        self._next_tick_update = custom_types.TimeStamp(new_dt.timestamp())

    def ready_with_auto_update(self, current_time: custom_types.TimeStamp):
        is_ready = self.ready(current_time=current_time)
        if not is_ready:
            return False
        else:
            self.update_next_tick(current_time=current_time)
            return True

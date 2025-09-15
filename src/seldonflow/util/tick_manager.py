from seldonflow.util import custom_types

from typing import List
from datetime import timedelta

ONE_MINUTE = custom_types.TimeStamp(60)
FIVE_MINUTES = custom_types.TimeStamp(300)
ONE_HOUR = custom_types.TimeStamp(3600)


class TickManager:
    def __init__(self, tick_interval: custom_types.TimeStamp):
        self._tick_interval = tick_interval
        self._next_tick_update = custom_types.TimeStamp(0.0)

    def ready(self, current_time: custom_types.TimeStamp):
        if current_time < self._next_tick_update:
            return False
        else:
            return True

    def update_next_tick(self, current_time: custom_types.TimeStamp):
        self._next_tick_update = current_time + self._tick_interval

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

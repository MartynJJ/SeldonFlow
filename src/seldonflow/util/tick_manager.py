from seldonflow.util import custom_types


class TickerManager:
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

    def ready_with_auto_update(self, current_time: custom_types.TimeStamp):
        is_ready = self.ready(current_time=current_time)
        if not is_ready:
            return False
        else:
            self.update_next_tick(current_time=current_time)
            return True

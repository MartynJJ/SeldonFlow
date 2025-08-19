from seldonflow.util.logger import LoggingMixin
from seldonflow.util import tick_manager, custom_types, custom_methods
from seldonflow.util.env import Environment


class ResearchManager(LoggingMixin):
    def __init__(self, env: Environment):
        super().__init__()
        self._tick_manager = tick_manager.TickManager(
            tick_interval=tick_manager.FIVE_MINUTES
        )
        self._env = env

    def on_tick(self, current_time: custom_types.TimeStamp):
        if not self._tick_manager.ready_with_auto_update(current_time=current_time):
            pass
        else:
            pass

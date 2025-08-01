from seldonflow.platform.platform import LivePlatform


class StrategyManager:
    _live_platform: LivePlatform

    def __init__(self, live_platform: LivePlatform):
        self._live_platform = live_platform

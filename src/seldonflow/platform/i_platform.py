from seldonflow.api_client.api_client import iApiClient
from seldonflow.util import logger, env

from abc import ABC, abstractmethod
from datetime import date


class iPlatform(ABC, logger.LoggingMixin):
    def __init__(self, environment: env.Environment):
        super().__init__()
        self._env = environment
        logger.setup_logging(
            log_file=str(logger.get_log_file_path(self._env)), log_level="DEBUG"
        )
        self.logger.debug(f"{self.__class__.__name__} Initialized in {self._env.value}")

    @abstractmethod
    def api_client(self) -> iApiClient:
        pass

    @abstractmethod
    def today(self) -> date:
        pass

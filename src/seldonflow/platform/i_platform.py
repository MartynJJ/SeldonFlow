from seldonflow.api_client.api_client import iApiClient

from abc import ABC, abstractmethod
from datetime import date


class iPlatform(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def api_client(self) -> iApiClient:
        pass

    @abstractmethod
    def today(self) -> date:
        pass

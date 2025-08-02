from seldonflow.api_client.api_client import iApiClient

from abc import ABC, abstractmethod


class iPlatform(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def api_client(self) -> iApiClient:
        pass

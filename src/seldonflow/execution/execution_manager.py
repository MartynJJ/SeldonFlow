from seldonflow.api_client.api_client import iApiClient


class ExecutionManager:
    _api_client: iApiClient

    def __init__(self, api_client: iApiClient):
        self._api_client = api_client

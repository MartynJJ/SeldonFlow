from enum import Enum


class Environment(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

    @staticmethod
    def from_string(env_str: str):
        if env_str.lower() == "development":
            return Environment.DEVELOPMENT
        elif env_str.lower() == "production":
            return Environment.PRODUCTION
        elif env_str.lower() == "testing":
            return Environment.TESTING
        else:
            raise ValueError(f"Unknown environment: {env_str}")

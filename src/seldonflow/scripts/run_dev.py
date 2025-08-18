from seldonflow.platform.platform import LivePlatform
from seldonflow.util.env import Environment

ENV = Environment.TESTING
# ENV = Environment.PRODUCTION


def main():
    print("SeldonFlow Platform starting...")
    live_platform = LivePlatform(ENV)
    live_platform.enable()


if __name__ == "__main__":
    main()

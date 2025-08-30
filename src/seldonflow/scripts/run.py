from seldonflow.platform.platform import LivePlatform
from seldonflow.util.env import Environment

import time

# ENV = Environment.TESTING
ENV = Environment.PRODUCTION


def enable_platform():
    live_platform = LivePlatform(ENV)
    live_platform.enable()


def main():
    print("SeldonFlow Platform starting...")
    while True:
        try:
            enable_platform()

        except KeyboardInterrupt as key:
            print("Killing from keyboard interupt")
            raise

        except Exception as e:
            print(f"Error in platform, pausing for 1 min and restarting {e}")
            time.sleep(60)
            continue


if __name__ == "__main__":
    main()

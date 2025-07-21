from seldonflow.platform.platform import LivePlatform


def main():
    print("SeldonFlow Platform starting...")
    live_platform = LivePlatform()
    live_platform.enable()


if __name__ == "__main__":
    main()

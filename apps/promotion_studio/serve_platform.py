"""Start the local simulated publishing platform for Promotion Studio."""

import argparse

from promotion_publish import serve_platform


def main():
    parser = argparse.ArgumentParser(description="Promotion Studio local simulated platform")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument("--data", default="./local-platform-data")
    args = parser.parse_args()
    serve_platform(args.host, args.port, args.data)


if __name__ == "__main__":
    main()

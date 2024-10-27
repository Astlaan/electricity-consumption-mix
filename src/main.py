import logging

logging.getLogger("matplotlib").setLevel(logging.WARNING)

import argparse
import pandas as pd
from datetime import datetime
from data_fetcher import ENTSOEDataFetcher
from utils import validate_inputs


def main():
    args = parse_arguments()
    if not validate_inputs(args):
        return

    data_fetcher = ENTSOEDataFetcher()

    if args.reset_cache:
        data_fetcher.reset_cache()

    start_date = args.start_date
    end_date = args.end_date

    data = data_fetcher.get_data(start_date, end_date)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Electricity Consumption Share Calculator for Portugal"
    )
    parser.add_argument(
        "--start_date",
        required=True,
        type=parse_datetime,
        help="Start date (YYYY-MM-DD) or datetime (YYYY-MM-DDTHH:MM:SS)",
    )
    parser.add_argument(
        "--end_date",
        required=True,
        type=parse_datetime,
        help="End date (YYYY-MM-DD) or datetime (YYYY-MM-DDTHH:MM:SS)",
    )
    parser.add_argument(
        "--visualization",
        choices=["none", "simple", "detailed", "nested"],
        default="none",
        help="Type of visualization to generate",
    )
    parser.add_argument(
        "--reset-cache", action="store_true", help="Reset the data cache"
    )  # Changed from reset_cache to reset-cache
    return parser.parse_args()


def parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"Invalid date or datetime format: {value}. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS."
            )


if __name__ == "__main__":
    main()

# Example usage:
# python src\main.py --start_date 2015-01-01 --end_date 2015-12-31 --visualization simple

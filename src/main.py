import argparse
import os
from datetime import datetime
from data_fetcher import ENTSOEDataFetcher
from calculator import ElectricityMixCalculator
from utils import validate_inputs, aggregate_results

def main():
    parser = argparse.ArgumentParser(description="Electricity Consumption Share Calculator for Portugal")
    parser.add_argument("--start_date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--granularity", choices=["hourly", "daily", "weekly", "monthly"], default="daily")
    parser.add_argument("--include_france", action="store_true", help="Include French contribution")
    args = parser.parse_args()

    if not validate_inputs(args):
        return

    security_token = "89fec152-d36b-49c8-b0b6-4e67e57b26ea"
    data_fetcher = ENTSOEDataFetcher(security_token)
    calculator = ElectricityMixCalculator()

    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

    pt_data = data_fetcher.get_portugal_data(start_date, end_date)
    es_data = data_fetcher.get_spain_data(start_date, end_date)
    fr_data = data_fetcher.get_france_data(start_date, end_date) if args.include_france else None

    results = calculator.calculate_mix(pt_data, es_data, fr_data, args.include_france)
    aggregated_results = aggregate_results(results, args.granularity)

    print(aggregated_results)

if __name__ == "__main__":
    main()

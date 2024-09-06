import argparse
import os
import logging
from datetime import datetime
from data_fetcher import ENTSOEDataFetcher
from calculator import ElectricityMixCalculator
from utils import validate_inputs, aggregate_results

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='electricity_mix_calculator.log')
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def save_results_to_csv(results, filename):
    results.to_csv(filename)
    logging.info(f"Results saved to {filename}")

def main():
    setup_logging()
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

    # Save results to CSV
    output_filename = f"electricity_mix_{args.start_date}_{args.end_date}_{args.granularity}.csv"
    save_results_to_csv(aggregated_results, output_filename)

if __name__ == "__main__":
    main()

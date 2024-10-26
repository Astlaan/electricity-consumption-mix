import logging
logging.getLogger('matplotlib').setLevel(logging.WARNING)

import asyncio
import argparse
import pandas as pd
from datetime import datetime
from data_fetcher import ENTSOEDataFetcher
from calculator import ElectricityMixCalculator
from utils import validate_inputs, aggregate_results
from visualizer import ElectricityMixVisualizer

async def fetch_data(fetcher, country, start_date, end_date):
    print(f"Fetching {country} data...")
    if country == "Portugal":
        generation = await fetcher.get_generation_data_async('10YPT-REN------W', start_date, end_date)
        imports = await fetcher.get_physical_flows_async('10YES-REE------0', '10YPT-REN------W', start_date, end_date)
        exports = await fetcher.get_physical_flows_async('10YPT-REN------W', '10YES-REE------0', start_date, end_date)
        return {'generation': generation, 'imports': imports, 'exports': exports}
    elif country == "Spain":
        generation = await fetcher.get_generation_data_async('10YES-REE------0', start_date, end_date)
        return {'generation': generation}
    else:
        raise ValueError(f"Unsupported country: {country}")

async def main():
    args = parse_arguments()
    if not validate_inputs(args):
        return

    data_fetcher = ENTSOEDataFetcher()
    
    if args.reset_cache:
        data_fetcher.reset_cache()

    start_date = args.start_date
    end_date = args.end_date

    try:
        pt_data = await fetch_data(data_fetcher, "Portugal", start_date, end_date)
        es_data = await fetch_data(data_fetcher, "Spain", start_date, end_date)

        # print_data_summary(pt_data, "Portugal")
        # print_data_summary(es_data, "Spain")

        # Calculate and print electricity mix
        calculator = ElectricityMixCalculator()
        results = calculator.calculate_mix(pt_data, es_data)
        # print_results(results, args)

    except Exception as e:
        print(f"An error occurred: {str(e)}")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Electricity Consumption Share Calculator for Portugal")
    parser.add_argument("--start_date", required=True, type=parse_datetime, 
                       help="Start date (YYYY-MM-DD) or datetime (YYYY-MM-DDTHH:MM:SS)")
    parser.add_argument("--end_date", required=True, type=parse_datetime, 
                       help="End date (YYYY-MM-DD) or datetime (YYYY-MM-DDTHH:MM:SS)")
    parser.add_argument("--visualization", choices=['none', 'simple', 'detailed', 'nested'],
                       default='none', help="Type of visualization to generate")
    parser.add_argument("--reset_cache", action='store_true', help="Reset the data cache")
    return parser.parse_args()

def parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid date or datetime format: {value}. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.")

def print_data_summary(data, country):
    print(f"\n{country} data:")
    for key, df in data.items():
        print(f"{key}:")
        print(f"  Shape: {df.shape}")
        print(f"  Columns: {df.columns.tolist()}")
        if not df.empty:
            print(f"  Date range: {df['start_time'].min()} to {df['start_time'].max()}")
            print(f"  Sample data:\n{df.head()}\n")
        else:
            print("  DataFrame is empty\n")

def print_results(results, args):
    pass #Function body removed because it was entirely commented out

if __name__ == "__main__":
    asyncio.run(main())

# Example usage:
# python src\main.py --start_date 2015-01-01 --end_date 2015-12-31 --visualization simple

import logging
logging.getLogger('matplotlib').setLevel(logging.WARNING)

import asyncio
import argparse
import pandas as pd
from datetime import datetime
from data_fetcher import ENTSOEDataFetcher
from utils import validate_inputs, aggregate_results
from analyzer import ElectricityMixAnalyzer

async def fetch_data(fetcher, country, start_date, end_date):
    print(f"Fetching {country} data...")
    try:
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
    except Exception as e:
        print(f"Error fetching data for {country}: {e}")
        return {}


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

        # Analyze and visualize electricity mix
        analyzer = ElectricityMixAnalyzer()
        if args.visualization != 'none':
            analyzer.analyze_and_visualize(pt_data, es_data, args.visualization)

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
    parser.add_argument("--reset-cache", action='store_true', help="Reset the data cache")  # Changed from reset_cache to reset-cache
    return parser.parse_args()

def parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid date or datetime format: {value}. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.")


if __name__ == "__main__":
    asyncio.run(main())

# Example usage:
# python src\main.py --start_date 2015-01-01 --end_date 2015-12-31 --visualization simple

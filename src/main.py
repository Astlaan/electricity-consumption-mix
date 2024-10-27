import logging
logging.getLogger('matplotlib').setLevel(logging.WARNING)

import asyncio
import argparse
import pandas as pd
from datetime import datetime
from data_fetcher import ENTSOEDataFetcher
from utils import validate_inputs, aggregate_results
from analyzer import ElectricityMixAnalyzer

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
        # Fetch all data in parallel
        data = await data_fetcher.get_data(start_date, end_date)
        
        # Create data dictionaries in the format expected by analyzer
        pt_data = {
            'generation': data.generation_pt,
            'imports': data.flow_es_to_pt,
            'exports': data.flow_pt_to_es
        }
        
        es_data = {
            'generation': data.generation_es
        }

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

import argparse
import pandas as pd
from datetime import datetime
import logging
from data_fetcher import ENTSOEDataFetcher
from calculator import ElectricityMixCalculator
from utils import validate_inputs, aggregate_results

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    args = parse_arguments()
    if not validate_inputs(args):
        return

    data_fetcher = ENTSOEDataFetcher("89fec152-d36b-49c8-b0b6-4e67e57b26ea")
    calculator = ElectricityMixCalculator()

    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

    logger.info(f"Processing data from {start_date} to {end_date}")

    try:
        pt_data = fetch_data(data_fetcher, "Portugal", start_date, end_date)
        es_data = fetch_data(data_fetcher, "Spain", start_date, end_date)

        print_data_summary(pt_data, "Portugal")
        print_data_summary(es_data, "Spain")

        # Check if we have data for the full date range
        for country, data in [("Portugal", pt_data), ("Spain", es_data)]:
            for key, df in data.items():
                if df.empty:
                    logger.warning(f"{country} {key} data is empty")
                else:
                    date_range = pd.date_range(start=start_date, end=end_date, freq='H')
                    missing_dates = date_range.difference(df['start_time'].dt.floor('H'))
                    if not missing_dates.empty:
                        logger.warning(f"{country} {key} data is missing dates: {missing_dates}")

        if all(df.empty for df in pt_data.values()) and all(df.empty for df in es_data.values()):
            logger.error("All DataFrames are empty. Cannot proceed with calculations.")
            return

        logger.info("Calculating electricity mix")
        pt_results = calculator.calculate_mix(pt_data, es_data)
        if pt_results is not None and not pt_results.empty:
            logger.info(f"Results shape: {pt_results.shape}")
            logger.info(f"Results date range: {pt_results.index.min()} to {pt_results.index.max()}")
            print_results(pt_results, args.granularity)
        else:
            logger.error("Unable to calculate electricity mix. The result is empty or None.")

    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Electricity Consumption Share Calculator for Portugal")
    parser.add_argument("--start_date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--granularity", default="hourly", choices=["hourly", "daily", "weekly", "monthly"], help="Time granularity for results")
    return parser.parse_args()

def fetch_data(fetcher, country, start_date, end_date):
    logger.info(f"Fetching {country} data...")
    if country == "Portugal":
        return fetcher.get_portugal_data(start_date, end_date)
    elif country == "Spain":
        return fetcher.get_spain_data(start_date, end_date)

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

def print_results(results, granularity):
    if results is None or results.empty:
        logger.error("No results to display")
        return

    logger.info("Aggregating results...")
    aggregated_results = aggregate_results(results, granularity)

    print(f"\nPortugal's Electricity Mix ({granularity} granularity):")
    print(f"Date range: {aggregated_results.index.min()} to {aggregated_results.index.max()}")
    print(f"Number of periods: {len(aggregated_results)}")
    print(f"Energy sources: {aggregated_results.columns.tolist()}")
    print("\nSample of results (percentages):")
    print(aggregated_results.head().applymap(lambda x: f"{x:.2f}%"))
    
    print("\nSummary statistics (percentages):")
    print(aggregated_results.describe().applymap(lambda x: f"{x:.2f}%"))

    # Additional data quality checks
    print("\nData quality checks:")
    print(f"Any NaN values: {aggregated_results.isna().any().any()}")
    print(f"Any negative values: {(aggregated_results < 0).any().any()}")
    print(f"Any values > 100%: {(aggregated_results > 100).any().any()}")
    print(f"Row sums (should be close to 100%):")
    print(aggregated_results.sum(axis=1).describe().apply(lambda x: f"{x:.2f}%"))

if __name__ == "__main__":
    main()

# Example usage:
# python src\main.py --start_date 2024-01-01 --end_date 2024-03-31 --granularity hourly

import argparse
import pandas as pd
from datetime import datetime
from data_fetcher import ENTSOEDataFetcher
from calculator import ElectricityMixCalculator
from utils import validate_inputs, aggregate_results

def main():
    args = parse_arguments()
    if not validate_inputs(args):
        return

    data_fetcher = ENTSOEDataFetcher("89fec152-d36b-49c8-b0b6-4e67e57b26ea")

    start_date = datetime(2024, 1, 1, 0, 0)
    end_date = datetime(2024, 1, 1, 1, 0)

    try:
        pt_data = fetch_data(data_fetcher, "Portugal", start_date, end_date)
        es_data = fetch_data(data_fetcher, "Spain", start_date, end_date)

        print("\nPortugal data:")
        for key, df in pt_data.items():
            print(f"\n{key.capitalize()}:")
            print(df.to_string())

        print("\nSpain data:")
        for key, df in es_data.items():
            print(f"\n{key.capitalize()}:")
            print(df.to_string())

    except Exception as e:
        print(f"An error occurred: {str(e)}")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Electricity Consumption Share Calculator for Portugal")
    parser.add_argument("--start_date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--granularity", default="hourly", choices=["hourly", "daily", "weekly", "monthly"], help="Time granularity for results")
    return parser.parse_args()

def fetch_data(fetcher, country, start_date, end_date):
    print(f"Fetching {country} data...")
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
        print("No results to display")
        return

    print("Aggregating results...")
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

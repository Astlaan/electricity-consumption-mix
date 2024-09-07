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

    start_date = args.start_date
    end_date = args.end_date

    try:
        pt_data = fetch_data(data_fetcher, "Portugal", start_date, end_date)
        es_data = fetch_data(data_fetcher, "Spain", start_date, end_date)

        print_data_summary(pt_data, "Portugal")
        print_data_summary(es_data, "Spain")

        # Calculate and print electricity mix
        calculator = ElectricityMixCalculator()
        results = calculator.calculate_mix(pt_data, es_data)
        print_results(results, args.granularity)

    except Exception as e:
        print(f"An error occurred: {str(e)}")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Electricity Consumption Share Calculator for Portugal")
    parser.add_argument("--start_date", required=True, type=parse_datetime, help="Start date (YYYY-MM-DD) or datetime (YYYY-MM-DDTHH:MM:SS)")
    parser.add_argument("--end_date", required=True, type=parse_datetime, help="End date (YYYY-MM-DD) or datetime (YYYY-MM-DDTHH:MM:SS)")
    parser.add_argument("--granularity", default="hourly", choices=["hourly", "daily", "weekly", "monthly"], help="Time granularity for results")
    return parser.parse_args()

def parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid date or datetime format: {value}. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.")

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
    
    print("\nFull results (percentages):")
    pd.set_option('display.max_columns', None)  # Show all columns
    pd.set_option('display.width', None)  # Don't wrap to multiple lines
    print(aggregated_results.applymap(lambda x: f"{x:.2f}%"))
    
    print("\nSummary statistics (percentages):")
    print(aggregated_results.describe().applymap(lambda x: f"{x:.2f}%"))

    # Additional data quality checks
    print("\nData quality checks:")
    print(f"Any NaN values: {aggregated_results.isna().any().any()}")
    print(f"Any negative values: {(aggregated_results < 0).any().any()}")
    print(f"Any values > 100%: {(aggregated_results > 100).any().any()}")
    print(f"Row sums (should be close to 100%):")
    print(aggregated_results.sum(axis=1).describe().apply(lambda x: f"{x:.2f}%"))

    # Debug log
    print("\nDEBUG: Full aggregated results dataframe:")
    print(aggregated_results)

if __name__ == "__main__":
    main()

# Example usage:
# python src\main.py --start_date 2024-01-01 --end_date 2024-03-31 --granularity hourly

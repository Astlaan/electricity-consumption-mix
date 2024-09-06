import argparse
from datetime import datetime
from data_fetcher import ENTSOEDataFetcher
from calculator import ElectricityMixCalculator
from utils import validate_inputs, aggregate_results

def main():
    parser = argparse.ArgumentParser(description="Electricity Consumption Share Calculator for Portugal")
    parser.add_argument("--start_date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--granularity", default="hourly", choices=["hourly", "daily", "weekly", "monthly"], help="Time granularity for results")
    args = parser.parse_args()

    if not validate_inputs(args):
        return

    security_token = "89fec152-d36b-49c8-b0b6-4e67e57b26ea"
    data_fetcher = ENTSOEDataFetcher(security_token)
    calculator = ElectricityMixCalculator()

    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

    try:
        pt_data = data_fetcher.get_portugal_data(start_date, end_date)
        es_data = data_fetcher.get_spain_data(start_date, end_date)

        print("Data fetched successfully.")
        print("\nPortugal data:")
        for key, df in pt_data.items():
            print(f"{key}:")
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {df.columns.tolist()}")
            print(f"  Date range: {df['start_time'].min()} to {df['start_time'].max()}")
            print(f"  Sample data:\n{df.head()}\n")

        print("\nSpain data:")
        for key, df in es_data.items():
            print(f"{key}:")
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {df.columns.tolist()}")
            print(f"  Date range: {df['start_time'].min()} to {df['start_time'].max()}")
            print(f"  Sample data:\n{df.head()}\n")

        print("\nCalculating electricity mix...")
        pt_results = calculator.calculate_mix(pt_data, es_data)
        
        print("\nAggregating results...")
        aggregated_results = aggregate_results(pt_results, args.granularity)

        print(f"\nPortugal's Electricity Mix ({args.granularity} granularity):")
        print(f"Date range: {aggregated_results.index.min()} to {aggregated_results.index.max()}")
        print(f"Number of periods: {len(aggregated_results)}")
        print(f"Energy sources: {aggregated_results.columns.tolist()}")
        print("\nSample of results:")
        print(aggregated_results.head(10))
        
        print("\nSummary statistics:")
        print(aggregated_results.describe())

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()

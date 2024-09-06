import argparse
import pandas as pd
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
        print("Fetching Portugal data...")
        pt_data = data_fetcher.get_portugal_data(start_date, end_date)
        print("Fetching Spain data...")
        es_data = data_fetcher.get_spain_data(start_date, end_date)

        print("Data fetched successfully.")
        print("\nPortugal data:")
        for key, df in pt_data.items():
            print(f"{key}:")
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {df.columns.tolist()}")
            if not df.empty:
                print(f"  Date range: {df['start_time'].min()} to {df['start_time'].max() + pd.Timedelta(hours=1)}")
                print(f"  Sample data:\n{df.head()}\n")
            else:
                print("  DataFrame is empty\n")

        print("\nSpain data:")
        for key, df in es_data.items():
            print(f"{key}:")
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {df.columns.tolist()}")
            if not df.empty:
                print(f"  Date range: {df['start_time'].min()} to {df['start_time'].max()}")
                print(f"  Sample data:\n{df.head()}\n")
            else:
                print("  DataFrame is empty\n")

        if any(df.empty for df in pt_data.values()) or any(df.empty for df in es_data.values()):
            print("Warning: Some DataFrames are empty. This may affect the calculation results.")
            for country, data in [("Portugal", pt_data), ("Spain", es_data)]:
                for key, df in data.items():
                    if df.empty:
                        print(f"  {country} {key} DataFrame is empty.")
        
        if all(df.empty for df in pt_data.values()) and all(df.empty for df in es_data.values()):
            print("Error: All DataFrames are empty. Cannot proceed with calculations.")
        else:
            print("\nCalculating electricity mix...")
            pt_results = calculator.calculate_mix(pt_data, es_data)
            
            if pt_results is not None and not pt_results.empty:
                print("\nAggregating results...")
                aggregated_results = aggregate_results(pt_results, args.granularity)

                print(f"\nPortugal's Electricity Mix ({args.granularity} granularity):")
                print(f"Date range: {aggregated_results.index.min()} to {aggregated_results.index.max() + pd.Timedelta(hours=1)}")
                print(f"Number of periods: {len(aggregated_results)}")
                print(f"Energy sources: {aggregated_results.columns.tolist()}")
                print("\nSample of results:")
                print(aggregated_results)
                
                print("\nSummary statistics:")
                print(aggregated_results.describe())
            else:
                print("Error: Unable to calculate electricity mix. The result is empty or None.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()

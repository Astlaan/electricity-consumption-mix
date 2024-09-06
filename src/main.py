import argparse
from datetime import datetime
from data_fetcher import ENTSOEDataFetcher
from calculator import ElectricityMixCalculator

def main():
    parser = argparse.ArgumentParser(description="Electricity Consumption Share Calculator for Portugal")
    parser.add_argument("--start_date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    security_token = "89fec152-d36b-49c8-b0b6-4e67e57b26ea"
    data_fetcher = ENTSOEDataFetcher(security_token)
    calculator = ElectricityMixCalculator()

    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

    pt_data = data_fetcher.get_portugal_data(start_date, end_date)
    es_data = data_fetcher.get_spain_data(start_date, end_date)

    print("Portugal data:")
    for key, df in pt_data.items():
        print(f"{key} shape: {df.shape}")
        print(f"{key} columns: {df.columns}")
        print(f"{key} head:\n{df.head()}\n")

    print("Spain data:")
    for key, df in es_data.items():
        print(f"{key} shape: {df.shape}")
        print(f"{key} columns: {df.columns}")
        print(f"{key} head:\n{df.head()}\n")

    pt_results = calculator.calculate_mix(pt_data, es_data)

    print("Portugal's Electricity Mix:")
    print(pt_results)

if __name__ == "__main__":
    main()

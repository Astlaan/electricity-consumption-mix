from datetime import datetime
import pandas as pd

def validate_inputs(args):
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        if start_date >= end_date:
            print("Error: Start date must be before end date.")
            return False
        return True
    except ValueError:
        print("Error: Invalid date format. Use YYYY-MM-DD.")
        return False

def aggregate_results(results, granularity):
    if granularity == 'hourly':
        return results
    elif granularity == 'daily':
        return results.resample('D').mean()
    elif granularity == 'weekly':
        return results.resample('W').mean()
    elif granularity == 'monthly':
        return results.resample('M').mean()
    else:
        raise ValueError(f"Invalid granularity: {granularity}")

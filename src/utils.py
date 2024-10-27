from datetime import datetime
import pandas as pd
from config import PSR_TYPE_MAPPING

def validate_inputs(args):
    if args.start_date >= args.end_date:
        print("Error: Start date must be before end date.")
        return False
    return True

def aggregate_results(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame(columns=list(PSR_TYPE_MAPPING.values()))
    
    # Map PSR types to their descriptions
    results = results.rename(columns=PSR_TYPE_MAPPING)
    

    return results


def get_active_psr_in_dataframe(df):
    return [col for col in df.columns if col in PSR_TYPE_MAPPING]

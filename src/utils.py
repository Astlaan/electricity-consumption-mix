from datetime import datetime
import pandas as pd
from config import PSR_TYPE_MAPPING

def validate_inputs(args):
    if args.start_date >= args.end_date:
        print("Error: Start date must be before end date.")
        return False
    return True

def get_active_psr_in_dataframe(df):
    return [col for col in df.columns if col in PSR_TYPE_MAPPING]

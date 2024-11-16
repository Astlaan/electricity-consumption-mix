from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Union
import pandas as pd
from config import PSR_TYPE_MAPPING
from dataclasses import dataclass, fields

RECORDS_START = datetime.fromisoformat("2015-01-10 00:00:00")



def current_day_start():
    return datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None)

def maximum_date_end_exclusive():
    """Returns the current UTC hour minus 1 hour as a naive datetime"""
    now = datetime.utcnow()  # Use utcnow() instead of now(timezone.utc)
    return now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)


def validate_inputs(start_date, end_date):
    def _assert_whole_hour(date):
        assert(date.minute == 0 and date.second == 0 and date.microsecond == 0)
 
    _assert_whole_hour(start_date)
    _assert_whole_hour(end_date)

    # Assert minimum interval of 1 hour
    assert end_date-start_date >= timedelta(hours=1), "Minimum interval has to be 1 hour"

    # Assert within records
    assert RECORDS_START <= start_date, f"Earliest date has to be {RECORDS_START}"
    assert end_date <= maximum_date_end_exclusive(), f"Latest end date has to be {maximum_date_end_exclusive()}"


def get_active_psr_in_dataframe(df):
    return [col for col in df.columns if col in PSR_TYPE_MAPPING]


def get_cache_filename(params: Dict[str, Any]) -> str:
    """Generate a unique filename for caching based on the request parameters."""
    document_type = params.get("documentType")
    
    if document_type == "A75":  # Generation data
        country_code = params.get("in_Domain")
        if not country_code:
            raise ValueError("Missing in_Domain for generation data")
        
        # Strip any special characters and use just the country part
        country = country_code.split('-')[0][-2:]  # Extract 'PT', 'ES', 'FR', etc.
        return f"generation_{country.lower()}"
        
    elif document_type == "A11":  # Flow data
        in_domain = params.get("in_Domain")
        out_domain = params.get("out_Domain")
        if not in_domain or not out_domain:
            raise ValueError("Missing in_Domain or out_Domain for flow data")
            
        # Extract country codes from the domain IDs
        in_country = in_domain.split('-')[0][-2:]  # Extract 'PT', 'ES', 'FR', etc.
        out_country = out_domain.split('-')[0][-2:]  # Extract 'PT', 'ES', 'FR', etc.
        
        return f"flow_{out_country.lower()}_to_{in_country.lower()}"
        
    else:
        raise ValueError(f"Unsupported document type: {document_type}")



def resample_to_standard_granularity(df: pd.DataFrame, granularity: timedelta) -> pd.DataFrame:
    if df.empty:
        return df

    # Set start_time as index for resampling
    df = df.set_index("start_time")

    # Get all numeric columns for resampling
    value_columns = df.select_dtypes(include=["float64", "int64"]).columns

    # Resample each value column
    resampled = (
        df[value_columns]
        .resample(
            granularity,
            offset="0h",  # Start periods at 00 minutes
            label="left",  # Use the start of the period as the label
            closed="left",  # Include the left boundary of the interval
        )
        .mean()
    )

    # Reset index to make start_time a column again
    resampled = resampled.reset_index()

    return resampled


def apply_to_fields(data, func):
    for field in fields(data):
        attr_name = field.name
        attr_value = getattr(data, attr_name)
        # Apply the transformation if it's necessary
        setattr(data, attr_name, func(attr_value))
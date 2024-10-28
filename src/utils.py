from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import pandas as pd
from config import PSR_TYPE_MAPPING


def validate_inputs(start_date, end_date):
    def _assert_exact_hour(dt):
        assert(dt.minute == 0 and dt.second == 0 and dt.microsecond == 0)

    _assert_exact_hour(start_date)
    _assert_exact_hour(end_date)

    assert(end_date-start_date >= timedelta(hours=1))

    current_day = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None)
    
    assert(start_date <= current_day)
    assert(end_date <= current_day)


def get_active_psr_in_dataframe(df):
    return [col for col in df.columns if col in PSR_TYPE_MAPPING]


def get_cache_filename(params: Dict[str, Any]) -> str:
    """Generate cache filename based on data type and countries."""
    document_type = params.get("documentType")
    in_domain = params.get("in_Domain", "")
    out_domain = params.get("out_Domain", "")

    if document_type == "A75":  # Generation data
        if "PT" in in_domain:
            return "generation_pt"
        elif "ES" in in_domain:
            return "generation_es"
    elif document_type == "A11":  # Flow data
        if "PT" in out_domain and "ES" in in_domain:
            return "flow_pt_to_es"
        elif "ES" in out_domain and "PT" in in_domain:
            return "flow_es_to_pt"

    raise ValueError(f"Unsupported combination of document type and domains")


def resample_to_standard_granularity(df: pd.DataFrame, granularity: timedelta) -> pd.DataFrame:
    if df.empty:
        return df

    # # Set start_time as index for resampling
    # df = df.set_index("start_time")

    # Get all numeric columns for resampling
    value_columns = df.select_dtypes(include=["float64", "int64"]).columns

    # Resample each value column
    resampled = (
        df[value_columns]
        .resample(
            granularity,
            offset="0H",  # Start periods at 00 minutes
            label="left",  # Use the start of the period as the label
            closed="left",  # Include the left boundary of the interval
        )
        .mean()
    )

    # # Reset index to make start_time a column again
    # resampled = resampled.reset_index()

    # Add end_time and resolution columns
    resampled["end_time"] = resampled.index + granularity
    resampled["resolution"] = granularity

    return resampled
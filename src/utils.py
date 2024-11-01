from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import pandas as pd
from config import PSR_TYPE_MAPPING

RECORDS_START = datetime.fromisoformat("2015-01-10 00:00:00")

def current_day_start():
    return datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None)

def validate_inputs(start_date, end_date):
    def _assert_exact_hour(date):
        assert(date.minute == 0 and date.second == 0 and date.microsecond == 0)

    def _assert_within_records(date):
        assert(RECORDS_START <= date)

    def _assert_less_or_equal_than_current_day_start(date):
        assert(date <= current_day_start())



    _assert_exact_hour(start_date)
    _assert_exact_hour(end_date)
    _assert_within_records(start_date)
    _assert_within_records(end_date)
    _assert_less_or_equal_than_current_day_start(start_date)
    _assert_less_or_equal_than_current_day_start(end_date)
    assert(end_date-start_date >= timedelta(hours=1))


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

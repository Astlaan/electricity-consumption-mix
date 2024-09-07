import pytest
from datetime import datetime
import pandas as pd
from utils import validate_inputs, aggregate_results, PSR_TYPE_MAPPING

class MockArgs:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

def test_validate_inputs_valid():
    args = MockArgs("2023-01-01", "2023-01-02")
    assert validate_inputs(args) == True

def test_validate_inputs_invalid_format():
    args = MockArgs("2023/01/01", "2023/01/02")
    assert validate_inputs(args) == False

def test_validate_inputs_end_before_start():
    args = MockArgs("2023-01-02", "2023-01-01")
    assert validate_inputs(args) == False

def test_validate_inputs_same_date():
    args = MockArgs("2023-01-01", "2023-01-01")
    assert validate_inputs(args) == False

def test_aggregate_results_hourly():
    df = pd.DataFrame({
        'B01': [1, 2, 3],
        'B02': [4, 5, 6]
    }, index=pd.date_range("2023-01-01", periods=3, freq="H"))
    result = aggregate_results(df, 'hourly')
    expected = df.rename(columns=PSR_TYPE_MAPPING)
    pd.testing.assert_frame_equal(result, expected)

def test_aggregate_results_daily():
    df = pd.DataFrame({
        'B01': [1, 2, 3, 4],
        'B02': [5, 6, 7, 8]
    }, index=pd.date_range("2023-01-01", periods=4, freq="6H"))
    result = aggregate_results(df, 'daily')
    expected = pd.DataFrame({
        'Biomass': [2.5],
        'Fossil Brown coal/Lignite': [6.5]
    }, index=pd.date_range("2023-01-01", periods=1, freq="D"))
    pd.testing.assert_frame_equal(result, expected)

def test_aggregate_results_invalid_granularity():
    df = pd.DataFrame({'B01': [1, 2, 3]})
    with pytest.raises(ValueError, match="Invalid granularity: yearly"):
        aggregate_results(df, 'yearly')

def test_aggregate_results_empty_dataframe():
    df = pd.DataFrame()
    result = aggregate_results(df, 'daily')
    assert result.empty
    assert result.columns.tolist() == list(PSR_TYPE_MAPPING.values())

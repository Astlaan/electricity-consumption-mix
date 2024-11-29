import unittest
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta, timezone
import pandas as pd
import logging
import os
import shutil
from src.data_fetcher import ENTSOEDataFetcher
import sys
import os
import asyncio
import aiohttp
from .test_data import test_data
from utils import AdvancedPattern
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

logger = logging.getLogger(__name__)


class TestENTSOEDataFetcher(unittest.TestCase):
    def test_get_data_for_pattern_cache_hit(self):
        """Test pattern-based data fetch when all data is in cache"""
        # Create mock cached data
        mock_data = pd.DataFrame({
            'start_time': pd.date_range('2024-01-01', '2024-01-02', freq='H'),
            '10YPT-REN------W': [100] * 24,  # PT generation
            '10YES-REE------0': [200] * 24,  # ES generation
            '10YPT-REN------W_10YES-REE------0': [300] * 24,  # PT to ES flow
            '10YES-REE------0_10YPT-REN------W': [400] * 24   # ES to PT flow
        }).set_index('start_time')

        self.fetcher.cached_data = mock_data

        pattern = AdvancedPattern(
            years="2024",
            months="1",
            days="1",
            hours="0-12"
        )

        with patch.object(self.fetcher, '_fetch_all_data') as mock_fetch:
            result = self.fetcher.get_data_for_pattern(pattern)

            # Verify no new data was fetched
            mock_fetch.assert_not_called()

            # Verify filtered data
            self.assertEqual(len(result.generation_pt), 12)  # Only 0-12 hours
            self.assertTrue(all(idx.hour < 12 for idx in result.generation_pt.index))

    def test_get_data_for_pattern_cache_miss(self):
        """Test pattern-based data fetch when cache needs updating"""
        # Create mock cached data with older dates
        mock_data = pd.DataFrame({
            'start_time': pd.date_range('2023-01-01', '2023-01-02', freq='H'),
            '10YPT-REN------W': [100] * 24,
            '10YES-REE------0': [200] * 24,
            '10YPT-REN------W_10YES-REE------0': [300] * 24,
            '10YES-REE------0_10YPT-REN------W': [400] * 24
        }).set_index('start_time')

        self.fetcher.cached_data = mock_data

        pattern = AdvancedPattern(
            years="2024",  # Request newer data than what's in cache
            months="1",
            days="1",
            hours="0-23"
        )

        with patch.object(self.fetcher, '_fetch_all_data') as mock_fetch:
            with patch.object(self.fetcher, '_load_cached_data') as mock_load:
                # Setup mock for new data after fetch
                new_data = pd.DataFrame({
                    'start_time': pd.date_range('2024-01-01', '2024-01-02', freq='H'),
                    '10YPT-REN------W': [100] * 24,
                    '10YES-REE------0': [200] * 24,
                    '10YPT-REN------W_10YES-REE------0': [300] * 24,
                    '10YES-REE------0_10YPT-REN------W': [400] * 24
                }).set_index('start_time')
                mock_load.return_value = new_data

                result = self.fetcher.get_data_for_pattern(pattern)

                # Verify fetch was called
                mock_fetch.assert_called_once()

                # Verify results match pattern
                self.assertEqual(len(result.generation_pt), 24)
                self.assertTrue(all(idx.year == 2024 for idx in result.generation_pt.index))

    def test_get_data_for_pattern_complex(self):
        """Test pattern-based data fetch with complex pattern"""
        mock_data = pd.DataFrame({
            'start_time': pd.date_range('2024-01-01', '2024-02-28', freq='H'),
            '10YPT-REN------W': [100] * (24 * 59),
            '10YES-REE------0': [200] * (24 * 59),
            '10YPT-REN------W_10YES-REE------0': [300] * (24 * 59),
            '10YES-REE------0_10YPT-REN------W': [400] * (24 * 59)
        }).set_index('start_time')

        self.fetcher.cached_data = mock_data

        pattern = AdvancedPattern(
            years="2024",
            months="1,2",
            days="1,15",
            hours="9-17"  # Business hours
        )

        result = self.fetcher.get_data_for_pattern(pattern)

        # Verify filtered data matches pattern
        for idx in result.generation_pt.index:
            self.assertEqual(idx.year, 2024)
            self.assertIn(idx.month, [1, 2])
            self.assertIn(idx.day, [1, 15])
            self.assertTrue(9 <= idx.hour < 17)

    def test_get_data_for_pattern_empty_result(self):
        """Test pattern-based data fetch when no data matches pattern"""
        mock_data = pd.DataFrame({
            'start_time': pd.date_range('2023-01-01', '2023-01-02', freq='H'),
            '10YPT-REN------W': [100] * 24,
            '10YES-REE------0': [200] * 24,
            '10YPT-REN------W_10YES-REE------0': [300] * 24,
            '10YES-REE------0_10YPT-REN------W': [400] * 24
        }).set_index('start_time')

        self.fetcher.cached_data = mock_data

        pattern = AdvancedPattern(
            years="2025",  # Year not in cache
            months="1",
            days="1",
            hours="0-23"
        )

        with self.assertRaises(ValueError) as context:
            self.fetcher.get_data_for_pattern(pattern)

        self.assertIn("No data found", str(context.exception))

    def setUp(self):
        self.fetcher = ENTSOEDataFetcher()
        # Clear the cache before each test
        if os.path.exists(self.fetcher.CACHE_DIR):
            shutil.rmtree(self.fetcher.CACHE_DIR)
        os.makedirs(self.fetcher.CACHE_DIR)
        os.environ["ENTSOE_TESTING"] = "true"
        self.fetcher = ENTSOEDataFetcher()
        # Clear the cache before each test
        if os.path.exists(self.fetcher.CACHE_DIR):
            shutil.rmtree(self.fetcher.CACHE_DIR)
        os.makedirs(self.fetcher.CACHE_DIR)
        os.environ["ENTSOE_TESTING"] = "true"

    def tearDown(self):
        os.environ.pop("ENTSOE_TESTING", None)

    def test_request_before_records(self):
        self.fetcher = ENTSOEDataFetcher()

        params = {
            "documentType": "A75",
            "processType": "A16",
            "in_Domain": "10YES-REE------0",
            "outBiddingZone_Domain": "10YES-REE------0",
            "periodStart": "200001010000",
            "periodEnd": "200001020000",
        }

        xml_data = self.fetcher._make_request(params)
        df = self.fetcher._parse_xml_to_dataframe(xml_data)
        assert df.empty == True

    def test_request_generation_pt(self):
        self.fetcher = ENTSOEDataFetcher()

        params = {
            "documentType": "A75",
            "processType": "A16",
            "in_Domain": "10YPT-REN------W",
            "outBiddingZone_Domain": "10YPT-REN------W",
            "periodStart": "202401010000",
            "periodEnd": "202401010100",  
        }

        # params['documentType'] = ""

        xml_data = self.fetcher._make_request(params)
        df = self.fetcher._parse_xml_to_dataframe(xml_data)
        print(df)
        assert df.empty == False

    def test_request_generation_es(self):
        self.fetcher = ENTSOEDataFetcher()

        params = {
            "documentType": "A75",
            "processType": "A16",
            "in_Domain": "10YES-REE------0",
            "outBiddingZone_Domain": "10YES-REE------0",
            "periodStart": "202401010000",
            "periodEnd": "202401010100",  
        }

        # params['documentType'] = ""

        xml_data = self.fetcher._make_request(params)
        print(xml_data)
        df = self.fetcher._parse_xml_internal(xml_data)
        print(df["B10"])
        assert df.empty == False

    def test_request_flow_pt_to_es(self):
        self.fetcher = ENTSOEDataFetcher()

        params = {
            "documentType": "A11",
            "out_Domain": "10YPT-REN------W",
            "in_Domain": "10YES-REE------0",
            "periodStart": "202401010000",
            "periodEnd": "202401010100",  # 1 day
        }

        xml_data = self.fetcher._make_request(params)
        df = self.fetcher._parse_xml_to_dataframe(xml_data)
        print(df)
        assert df.empty == False

    def test_request_flow_es_to_pt(self):
        self.fetcher = ENTSOEDataFetcher()

        params = {
            "documentType": "A11",
            "out_Domain": "10YES-REE------0",
            "in_Domain": "10YPT-REN------W",
            "periodStart": "202401010000",
            "periodEnd": "202401020000",  # 1 day
        }

        xml_data = self.fetcher._make_request(params)
        print(xml_data)
        df = self.fetcher._parse_xml_to_dataframe(xml_data)
        print(df)
        assert df.empty == False

    def test_parse_xml_to_dataframe(self):
        xml_data = """
        <GL_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0">
          <TimeSeries>
            <MktPSRType>
              <psrType>B01</psrType>
            </MktPSRType>
            <Period>
              <timeInterval>
                <start>2022-01-01T00:00Z</start>
              </timeInterval>
              <resolution>PT60M</resolution>
              <Point>
                <position>1</position>
                <quantity>100</quantity>
              </Point>
            </Period>
          </TimeSeries>
        </GL_MarketDocument>
        """

        result = self.fetcher._parse_xml_to_dataframe(xml_data)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["psr_type"], "B01")
        self.assertEqual(result.iloc[0]["quantity"], 100.0)

    @patch("aiohttp.ClientSession.get")
    def test_get_generation_data(self, mock_get):
        # Create a mock response that acts as an async context manager
        mock_response = AsyncMock()
        mock_response.text.return_value = "<dummy>XML</dummy>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        start_date = datetime(2022, 1, 1)
        end_date = datetime(2022, 1, 2)
        result = self.fetcher.get_generation_data(
            "10YPT-REN------W", start_date, end_date
        )
        self.assertIsInstance(result, pd.DataFrame)

    @patch.object(ENTSOEDataFetcher, "_make_request_async")
    def test_caching_full_hit(self, mock_make_request_async):
        # Setup mock response using AsyncMock
        mock_make_request_async.return_value = test_data.data_first_two_hours

        start_date = datetime(2024, 1, 1, 0, 0)
        end_date = datetime(2024, 1, 1, 2, 0)

        # First call
        result1 = self.fetcher.get_generation_data(
            "10YPT-REN------W", start_date, end_date
        )
        print(result1)

        # Reset mock to verify it's not called again
        mock_make_request_async.reset_mock()

        # Second call
        result2 = self.fetcher.get_generation_data(
            "10YPT-REN------W", start_date, end_date
        )

        mock_make_request_async.assert_not_called()
        pd.testing.assert_frame_equal(result1, result2)

    @patch.object(ENTSOEDataFetcher, "_make_request_async")
    def test_caching_partial_hit(self, mock_make_request_async):
        # Setup mock response using AsyncMock
        mock_make_request_async.return_value = test_data.data_first_two_hours

        country_code = "10YPT-REN------W"
        start_date_1 = datetime(2024, 1, 1, 0, 0)
        end_date_1 = datetime(2024, 1, 1, 2, 0)
        start_date_2 = datetime(2024, 1, 1, 1, 0)
        end_date_2 = datetime(2024, 1, 1, 3, 0)

        # First call
        result1 = self.fetcher.get_generation_data(
            country_code, start_date_1, end_date_1
        )
        self.assertEqual(mock_make_request_async.call_count, 1)

        # Second call
        result2 = self.fetcher.get_generation_data(
            country_code, start_date_2, end_date_2
        )
        self.assertEqual(mock_make_request_async.call_count, 2)
        # Get the arguments from the second call
        second_call_params = mock_make_request_async.call_args_list[1][0][1]
        expected_params = {
            "documentType": "A75",
            "processType": "A16",
            "in_Domain": country_code,
            "outBiddingZone_Domain": country_code,
            "periodStart": "202401010200",
            "periodEnd": "202401010300",
        }
        self.assertEqual(second_call_params, expected_params)

    @patch("aiohttp.ClientSession.get")
    def test_caching_different_params(self, mock_get):
        mock_response = AsyncMock()
        mock_response.text.return_value = "<dummy>XML</dummy>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        start_date1 = datetime(2022, 1, 1)
        end_date1 = datetime(2022, 1, 2)
        start_date2 = datetime(2022, 1, 3)
        end_date2 = datetime(2022, 1, 4)

        # First call
        self.fetcher.get_generation_data("10YPT-REN------W", start_date1, end_date1)
        self.assertEqual(mock_get.call_count, 1)

        # Second call with different parameters
        self.fetcher.get_generation_data("10YPT-REN------W", start_date2, end_date2)
        self.assertEqual(mock_get.call_count, 2)

    def test_cache_file_creation(self):
        start_date = datetime(2022, 1, 1)
        end_date = datetime(2022, 1, 2)

        # Clear cache before test
        shutil.rmtree(self.fetcher.CACHE_DIR, ignore_errors=True)
        os.makedirs(self.fetcher.CACHE_DIR)

        with patch("src.data_fetcher.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.text = """
            <GL_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0">
                <TimeSeries>
                    <MktPSRType>
                        <psrType>B01</psrType>
                    </MktPSRType>
                    <Period>
                        <timeInterval>
                            <start>2022-01-01T00:00Z</start>
                            <end>2022-01-02T00:00Z</end>
                        </timeInterval>
                        <resolution>PT60M</resolution>
                        <Point>
                            <position>1</position>
                            <quantity>100</quantity>
                        </Point>
                    </Period>
                </TimeSeries>
            </GL_MarketDocument>
            """
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = self.fetcher.get_generation_data(
                "10YPT-REN------W", start_date, end_date
            )

        # Check if cache files were created
        cache_files = os.listdir(self.fetcher.CACHE_DIR)
        self.assertTrue(
            any(file.endswith(".parquet") for file in cache_files),
            f"No .parquet file found in {cache_files}",
        )
        self.assertTrue(
            any(file.endswith("_metadata.json") for file in cache_files),
            f"No _metadata.json file found in {cache_files}",
        )

        # Check if the result is not empty
        self.assertFalse(result.empty, "The resulting DataFrame is empty")

    @patch.object(ENTSOEDataFetcher, "get_generation_data")
    def test_edge_case_date_ranges(self, mock_get_generation_data):
        def create_mock_data(start_date, end_date):
            return pd.DataFrame(
                {
                    "start_time": [start_date],
                    "end_time": [start_date + timedelta(hours=1)],
                    "psr_type": ["B01"],
                    "quantity": [100.0],
                    "resolution": [timedelta(hours=1)],
                }
            )

        test_cases = [
            (datetime(2020, 1, 1), datetime(2020, 12, 31)),
            (datetime(2021, 1, 1), datetime(2021, 12, 31)),
            (datetime(2020, 12, 31), datetime(2021, 1, 1)),
            (datetime(2020, 3, 1), datetime(2020, 3, 31)),
            (datetime(2020, 2, 1), datetime(2020, 2, 29)),
            (datetime(2021, 2, 1), datetime(2021, 2, 28)),
        ]

        for start_date, end_date in test_cases:
            mock_get_generation_data.return_value = create_mock_data(
                start_date, end_date
            )
            result = self.fetcher.get_generation_data(
                "10YPT-REN------W", start_date, end_date
            )
            self.assertFalse(
                result.empty, f"Empty result for date range: {start_date} to {end_date}"
            )

    @patch("src.data_fetcher.requests.get")
    def test_portugal_generation_data(self, mock_get):
        # Load mock response from file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(
            os.path.join(
                current_dir,
                "test_data",
                "AGGREGATED_GENERATION_PER_TYPE_202401010000-202401020000.xml",
            ),
            "r",
        ) as file:
            mock_response_text = file.read()

        mock_response = Mock()
        mock_response.text = mock_response_text
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 1, 3, 0)

        result = self.fetcher.get_generation_data(
            "10YPT-REN------W", start_date, end_date
        )

        # Check if the result matches the expected data in the file
        self.assertFalse(result.empty, "Expected non-empty result")
        self.assertEqual(
            result["start_time"].min(), pd.Timestamp("2024-01-01 00:00:00")
        )
        self.assertLess(result["start_time"].max(), pd.Timestamp("2024-01-01 03:00:00"))

        # Check if all expected PSR types are present
        expected_psr_types = {
            "B01",
            "B04",
            "B05",
            "B10",
            "B11",
            "B12",
            "B16",
            "B18",
            "B19",
            "B20",
        }
        actual_psr_types = set(result["psr_type"].unique())
        self.assertEqual(
            actual_psr_types,
            expected_psr_types,
            f"Mismatch in PSR types. Expected: {expected_psr_types}, Actual: {actual_psr_types}",
        )

        # Check if the resolution is correct
        self.assertTrue(
            all(result["resolution"] == pd.Timedelta("1 hour")),
            "Resolution should be 1 hour for all entries",
        )

    def test_spain_generation_data(self):
        start_date = datetime(2024, 1, 1, 0, 0)
        end_date = datetime(2024, 1, 1, 2, 0)

        fetcher = ENTSOEDataFetcher()
        result = fetcher.get_generation_data("10YES-REE------0", start_date, end_date)

        values = [5632, 5664, 5672, 5656, 5608, 5612, 5544, 5448]
        averages = [sum(values[i : i + 4]) / 4 for i in range(0, len(values), 4)]

        print("Averages for each set of 4 values:", averages)

        print(result)

    # These tests for data gaps need to be verified
    def test_check_data_gaps(self):
        # Create test data with known gaps
        start_date = datetime(2024, 1, 1, 0, 0)
        end_date = datetime(2024, 1, 1, 5, 0)

        # Create data with gaps from 2:00-3:00 and 4:00-5:00
        data = pd.DataFrame(
            {
                "start_time": [
                    datetime(2024, 1, 1, 0, 0),
                    datetime(2024, 1, 1, 1, 0),
                    datetime(2024, 1, 1, 3, 0),
                ],
                "end_time": [
                    datetime(2024, 1, 1, 1, 0),
                    datetime(2024, 1, 1, 2, 0),
                    datetime(2024, 1, 1, 4, 0),
                ],
                "psr_type": ["B01", "B01", "B01"],
                "quantity": [100.0, 200.0, 300.0],
                "resolution": [timedelta(hours=1)] * 3,
            }
        )

        gaps = self.fetcher.check_data_gaps(data, start_date, end_date)

        # Verify results
        self.assertTrue(gaps["has_gaps"])
        self.assertEqual(gaps["total_gaps"], 2)  # Two missing hours
        self.assertEqual(len(gaps["gap_periods"]), 2)
        self.assertAlmostEqual(
            gaps["coverage_percentage"], 60.0
        )  # 3 out of 5 hours present

        # Check first gap period
        self.assertEqual(gaps["gap_periods"][0]["start"], datetime(2024, 1, 1, 2, 0))
        self.assertEqual(gaps["gap_periods"][0]["end"], datetime(2024, 1, 1, 3, 0))

        # Check second gap period
        self.assertEqual(gaps["gap_periods"][1]["start"], datetime(2024, 1, 1, 4, 0))
        self.assertEqual(gaps["gap_periods"][1]["end"], datetime(2024, 1, 1, 5, 0))

    def test_check_data_gaps_empty_data(self):
        start_date = datetime(2024, 1, 1, 0, 0)
        end_date = datetime(2024, 1, 1, 5, 0)

        empty_df = pd.DataFrame(
            columns=["start_time", "end_time", "psr_type", "quantity", "resolution"]
        )
        gaps = self.fetcher.check_data_gaps(empty_df, start_date, end_date)

        self.assertTrue(gaps["has_gaps"])
        self.assertEqual(gaps["total_gaps"], 5)  # All 5 hours missing
        self.assertEqual(len(gaps["gap_periods"]), 1)  # One continuous gap
        self.assertEqual(gaps["coverage_percentage"], 0.0)

        # Check gap period
        self.assertEqual(gaps["gap_periods"][0]["start"], start_date)
        self.assertEqual(gaps["gap_periods"][0]["end"], end_date)

    def test_check_data_gaps_complete_data(self):
        start_date = datetime(2024, 1, 1, 0, 0)
        end_date = datetime(2024, 1, 1, 3, 0)

        complete_data = pd.DataFrame(
            {
                "start_time": [
                    datetime(2024, 1, 1, 0, 0),
                    datetime(2024, 1, 1, 1, 0),
                    datetime(2024, 1, 1, 2, 0),
                ],
                "end_time": [
                    datetime(2024, 1, 1, 1, 0),
                    datetime(2024, 1, 1, 2, 0),
                    datetime(2024, 1, 1, 3, 0),
                ],
                "psr_type": ["B01", "B01", "B01"],
                "quantity": [100.0, 200.0, 300.0],
                "resolution": [timedelta(hours=1)] * 3,
            }
        )

        gaps = self.fetcher.check_data_gaps(complete_data, start_date, end_date)

        self.assertFalse(gaps["has_gaps"])
        self.assertEqual(gaps["total_gaps"], 0)
        self.assertEqual(len(gaps["gap_periods"]), 0)
        self.assertEqual(gaps["coverage_percentage"], 100.0)

    def test_resampling_from_finer_granularity(self):
        # Create test data with 15-minute granularity
        start_date = datetime(2024, 1, 1, 0, 0)
        df = pd.DataFrame(
            {
                "start_time": [
                    start_date + timedelta(minutes=15 * i) for i in range(8)
                ],
                "end_time": [
                    start_date + timedelta(minutes=15 * (i + 1)) for i in range(8)
                ],
                "psr_type": ["B01"] * 8,
                "quantity": [100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0],
                "resolution": [timedelta(minutes=15)] * 8,
            }
        )

        print(df)
        result = self.fetcher._resample_to_standard_granularity(df)
        print(result)

        # Check that result has hourly granularity
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]["quantity"], 250.0)  # Average of all values
        self.assertEqual(result.iloc[1]["quantity"], 650.0)  # Average of all values
        self.assertEqual(result.iloc[0]["resolution"], timedelta(hours=1))
        self.assertEqual(result.iloc[1]["resolution"], timedelta(hours=1))

    def test_resampling_from_coarser_granularity(self):
        # Create test data with 2-hour granularity
        start_date = datetime(2024, 1, 1, 0, 0)
        df = pd.DataFrame(
            {
                "start_time": [start_date],
                "end_time": [start_date + timedelta(hours=2)],
                "psr_type": ["B01"],
                "quantity": [200.0],
                "resolution": [timedelta(hours=2)],
            }
        )

        with self.assertRaises(ValueError) as context:
            self.fetcher._resample_to_standard_granularity(df)

        self.assertTrue("Resolution must be 1 hour or less" in str(context.exception))

    # TODO: 
    # - full hit full range
    # - full hit partial range
    # - Cache exists, partial overlap (fetch date should be = to cache end)
    # - Cache exists, no overlap (fetch date should be = to cache end)
    # - Cache exists, no overlap with gap (fetch date should be = to cache end)
    # all of the above: returns desired range
    # def test__fetch_and_cache_data(self):
    #     pass


if __name__ == "__main__":
    unittest.main()

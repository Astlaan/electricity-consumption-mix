import unittest
from unittest.mock import patch, Mock
from datetime import datetime
import pandas as pd
import logging
import os
import shutil
from src.data_fetcher import ENTSOEDataFetcher

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestENTSOEDataFetcher(unittest.TestCase):
    def setUp(self):
        logger.debug("Setting up TestENTSOEDataFetcher")
        self.fetcher = ENTSOEDataFetcher("dummy_token")
        # Clear the cache before each test
        if os.path.exists(self.fetcher.CACHE_DIR):
            shutil.rmtree(self.fetcher.CACHE_DIR)
        os.makedirs(self.fetcher.CACHE_DIR)

    @patch('src.data_fetcher.requests.get')
    def test_make_request(self, mock_get):
        logger.debug("Running test_make_request")
        mock_response = Mock()
        mock_response.text = "<dummy>XML</dummy>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.fetcher._make_request({'param': 'value'})
        
        self.assertEqual(result, "<dummy>XML</dummy>")
        mock_get.assert_called_once()
        logger.debug("test_make_request completed")

    def test_parse_xml_to_dataframe(self):
        logger.debug("Running test_parse_xml_to_dataframe")
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
        self.assertEqual(result.iloc[0]['psr_type'], 'B01')
        self.assertEqual(result.iloc[0]['quantity'], 100.0)
        logger.debug("test_parse_xml_to_dataframe completed")

    @patch.object(ENTSOEDataFetcher, '_make_request')
    @patch.object(ENTSOEDataFetcher, '_parse_xml_to_dataframe')
    def test_get_generation_data(self, mock_parse, mock_request):
        logger.debug("Running test_get_generation_data")
        mock_request.return_value = "<dummy>XML</dummy>"
        mock_parse.return_value = pd.DataFrame({'dummy': [1, 2, 3]})

        start_date = datetime(2022, 1, 1)
        end_date = datetime(2022, 1, 2)
        result = self.fetcher.get_generation_data('10YPT-REN------W', start_date, end_date)

        self.assertIsInstance(result, pd.DataFrame)
        mock_request.assert_called_once()
        mock_parse.assert_called_once_with("<dummy>XML</dummy>")
        logger.debug("test_get_generation_data completed")

    @patch('src.data_fetcher.requests.get')
    def test_caching(self, mock_get):
        logger.debug("Running test_caching")
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

        start_date = datetime(2022, 1, 1)
        end_date = datetime(2022, 1, 2)

        # First call should make a request and cache the result
        logger.debug("Making first call to get_generation_data")
        result1 = self.fetcher.get_generation_data('10YPT-REN------W', start_date, end_date)
        self.assertIsInstance(result1, pd.DataFrame)
        mock_get.assert_called_once()
        logger.debug("First call completed")

        # Reset the mock
        mock_get.reset_mock()
        logger.debug("Mock reset")

        # Second call with the same parameters should use cached data
        logger.debug("Making second call to get_generation_data")
        result2 = self.fetcher.get_generation_data('10YPT-REN------W', start_date, end_date)
        self.assertIsInstance(result2, pd.DataFrame)
        mock_get.assert_not_called()  # The mock should not be called for the second request
        logger.debug("Second call completed")

        # Check if the results are the same
        pd.testing.assert_frame_equal(result1, result2)
        logger.debug("test_caching completed")

    @patch('src.data_fetcher.requests.get')
    def test_caching_different_params(self, mock_get):
        logger.debug("Running test_caching_different_params")
        mock_response = Mock()
        mock_response.text = "<dummy>XML</dummy>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        start_date1 = datetime(2022, 1, 1)
        end_date1 = datetime(2022, 1, 2)
        start_date2 = datetime(2022, 1, 3)
        end_date2 = datetime(2022, 1, 4)

        # First call
        self.fetcher.get_generation_data('10YPT-REN------W', start_date1, end_date1)
        self.assertEqual(mock_get.call_count, 1)

        # Second call with different parameters
        self.fetcher.get_generation_data('10YPT-REN------W', start_date2, end_date2)
        self.assertEqual(mock_get.call_count, 2)

        logger.debug("test_caching_different_params completed")

    def test_cache_file_creation(self):
        logger.debug("Running test_cache_file_creation")
        start_date = datetime(2022, 1, 1)
        end_date = datetime(2022, 1, 2)
        
        # Clear cache before test
        shutil.rmtree(self.fetcher.CACHE_DIR, ignore_errors=True)
        os.makedirs(self.fetcher.CACHE_DIR)

        with patch('src.data_fetcher.requests.get') as mock_get:
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

            result = self.fetcher.get_generation_data('10YPT-REN------W', start_date, end_date)

        # Check if cache files were created
        cache_files = os.listdir(self.fetcher.CACHE_DIR)
        self.assertTrue(any(file.endswith('.parquet') for file in cache_files), f"No .parquet file found in {cache_files}")
        self.assertTrue(any(file.endswith('_metadata.json') for file in cache_files), f"No _metadata.json file found in {cache_files}")

        # Check if the result is not empty
        self.assertFalse(result.empty, "The resulting DataFrame is empty")

        logger.debug("test_cache_file_creation completed")

    @patch('src.data_fetcher.requests.get')
    def test_edge_case_date_ranges(self, mock_get):
        logger.debug("Running test_edge_case_date_ranges")
        
        # Define mock response for the API call
        mock_response = Mock()
        mock_response.text = """
        <GL_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0">
          <TimeSeries>
            <MktPSRType>
              <psrType>B01</psrType>
            </MktPSRType>
            <Period>
              <timeInterval>
                <start>2020-01-01T00:00Z</start>
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

        # Test cases for different date ranges
        test_cases = [
            (datetime(2020, 1, 1), datetime(2020, 12, 31)),  # Leap year
            (datetime(2021, 1, 1), datetime(2021, 12, 31)),  # Non-leap year
            (datetime(2020, 1, 1), datetime(2020, 1, 1)),    # Same start and end date
            (datetime(2020, 12, 31), datetime(2021, 1, 1)),  # End of one year to start of next
            (datetime(2020, 3, 1), datetime(2020, 3, 31)),   # Month with 31 days
            (datetime(2020, 2, 1), datetime(2020, 2, 29)),   # February in a leap year
            (datetime(2021, 2, 1), datetime(2021, 2, 28)),   # February in a non-leap year
        ]

        for start_date, end_date in test_cases:
            logger.debug(f"Testing date range: {start_date} to {end_date}")
            result = self.fetcher.get_generation_data('10YPT-REN------W', start_date, end_date)
            self.assertIsInstance(result, pd.DataFrame)
            self.assertGreaterEqual(len(result), 1)  # Ensure the dataset is not empty
            logger.debug(f"Date range {start_date} to {end_date} passed")

        logger.debug("test_edge_case_date_ranges completed")

    @patch('src.data_fetcher.requests.get')
    def test_portugal_generation_data(self, mock_get):
        logger.debug("Running test_portugal_generation_data")
        
        # Load mock response from file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, 'test_data', 'AGGREGATED_GENERATION_PER_TYPE_202401010000-202401020000.xml'), 'r') as file:
            mock_response_text = file.read()

        mock_response = Mock()
        mock_response.text = mock_response_text
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        start_date = datetime(2024, 1, 1, 0, 0)
        end_date = datetime(2024, 1, 1, 3, 0)
        
        result = self.fetcher.get_generation_data('10YPT-REN------W', start_date, end_date)
        
        print("\nPortugal Generation Data for the first 4 hours of 2024:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(result.to_string(index=False))
        
        # Check if the result matches the first 4 hours of data in the file
        expected_data = result[result['start_time'] < pd.Timestamp('2024-01-01 03:00:00+0000')]
        
        # Count unique PSR types (now columns, excluding 'start_time', 'end_time', 'resolution', 'in_domain', 'out_domain')
        unique_psr_types = len(expected_data.columns) - 5
        
        # Add assertions to check the correctness of the parsed data
        self.assertEqual(len(expected_data), 4, f"Expected 4 data points (4 hours)")
        
        psr_types = set(expected_data.columns) - {'start_time', 'end_time', 'resolution', 'in_domain', 'out_domain'}
        print(f"Found PSR types: {psr_types}")
        print(f"Number of PSR types: {len(psr_types)}")
        
        for psr_type in psr_types:
            print(f"Values for {psr_type}: {expected_data[psr_type].unique()}")
        
        # Check start times and end times
        expected_start_times = [pd.Timestamp('2023-12-31 23:00:00+0000'), 
                                pd.Timestamp('2024-01-01 00:00:00+0000'), 
                                pd.Timestamp('2024-01-01 01:00:00+0000'),
                                pd.Timestamp('2024-01-01 02:00:00+0000')]
        expected_end_times = [pd.Timestamp('2024-01-01 00:00:00+0000'), 
                              pd.Timestamp('2024-01-01 01:00:00+0000'), 
                              pd.Timestamp('2024-01-01 02:00:00+0000'),
                              pd.Timestamp('2024-01-01 03:00:00+0000')]
        
        self.assertEqual(expected_data['start_time'].tolist(), expected_start_times, "Start times are incorrect")
        self.assertEqual(expected_data['end_time'].tolist(), expected_end_times, "End times are incorrect")
        
        self.assertTrue(all(expected_data['resolution'] == pd.Timedelta('1 hour')), "Resolution should be 1 hour for all entries")
        
        # Check if all expected PSR types are present
        expected_psr_types = {'B01', 'B04', 'B05', 'B10', 'B11', 'B12', 'B16', 'B18', 'B19', 'B20'}
        actual_psr_types = set(expected_data.columns) - {'start_time', 'end_time', 'resolution', 'in_domain', 'out_domain'}
        self.assertEqual(actual_psr_types, expected_psr_types, 
                         f"Mismatch in PSR types. Expected: {expected_psr_types}, Actual: {actual_psr_types}")
        
        # Check if any PSR types have all zero values
        zero_psr_types = [psr_type for psr_type in expected_psr_types if (expected_data[psr_type] == 0).all()]
        if zero_psr_types:
            print(f"Warning: The following PSR types have all zero values: {zero_psr_types}")
        
        logger.debug("test_portugal_generation_data completed")

    @patch('src.data_fetcher.requests.get')
    def test_spain_generation_data(self, mock_get):
        print("\nRunning test_spain_generation_data")
        
        # Load mock response from file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, 'test_data', 'SPAIN_GENERATION_202401010000-202401010200.xml'), 'r') as file:
            mock_response_text = file.read()

        mock_response = Mock()
        mock_response.text = mock_response_text
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        start_date = datetime(2024, 1, 1, 0, 0)
        end_date = datetime(2024, 1, 1, 2, 0)
        
        fetcher = ENTSOEDataFetcher("dummy_token")
        result = fetcher.get_generation_data('10YES-REE------0', start_date, end_date)
        
        print("\nSpain Generation Data for the first 2 hours of 2024:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(result.to_string(index=False))
        
        # Assertions
        self.assertFalse(result.empty, "Result DataFrame is empty")
        self.assertEqual(len(result), 2, "Expected 2 rows (2 hours) in the result")
        self.assertTrue(all(result['resolution'] == pd.Timedelta('1 hour')), "Resolution should be 1 hour for all entries")
        
        # Check start times and end times
        expected_start_times = [pd.Timestamp('2023-12-31 23:00:00+0000'), pd.Timestamp('2024-01-01 00:00:00+0000')]
        expected_end_times = [pd.Timestamp('2024-01-01 00:00:00+0000'), pd.Timestamp('2024-01-01 01:00:00+0000')]
        
        self.assertEqual(result['start_time'].tolist(), expected_start_times, "Start times are incorrect")
        self.assertEqual(result['end_time'].tolist(), expected_end_times, "End times are incorrect")
        
        # Check if all expected PSR types are present (you may need to adjust this based on the actual data)
        expected_psr_types = {'B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B09', 'B10', 'B11', 'B12', 'B13', 'B14', 'B15', 'B16', 'B17', 'B18', 'B19', 'B20'}
        actual_psr_types = set(result.columns) - {'start_time', 'end_time', 'resolution'}
        self.assertEqual(actual_psr_types, expected_psr_types, f"Mismatch in PSR types. Expected: {expected_psr_types}, Actual: {actual_psr_types}")
        
        # Check if any PSR types have all zero values
        zero_psr_types = [psr_type for psr_type in expected_psr_types if (result[psr_type] == 0).all()]
        if zero_psr_types:
            print(f"Warning: The following PSR types have all zero values: {zero_psr_types}")
        
        print("test_spain_generation_data completed")

if __name__ == '__main__':
    unittest.main()

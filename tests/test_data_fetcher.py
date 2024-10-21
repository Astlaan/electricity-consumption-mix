import unittest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
import pandas as pd
import logging
import os
import shutil
from src.api_token import API_TOKEN
from src.data_fetcher import ENTSOEDataFetcher
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestENTSOEDataFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = ENTSOEDataFetcher("dummy_token")
        # Clear the cache before each test
        if os.path.exists(self.fetcher.CACHE_DIR):
            shutil.rmtree(self.fetcher.CACHE_DIR)
        os.makedirs(self.fetcher.CACHE_DIR)

    @patch('src.data_fetcher.requests.get')
    def test_make_request(self, mock_get):
        mock_response = Mock()
        mock_response.text = "<dummy>XML</dummy>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.fetcher._make_request({'param': 'value'})
        
        self.assertEqual(result, "<dummy>XML</dummy>")
        mock_get.assert_called_once()

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
        self.assertEqual(result.iloc[0]['psr_type'], 'B01')
        self.assertEqual(result.iloc[0]['quantity'], 100.0)

    @patch.object(ENTSOEDataFetcher, '_make_request')
    @patch.object(ENTSOEDataFetcher, '_parse_xml_to_dataframe')
    def test_get_generation_data(self, mock_parse, mock_request):
        mock_request.return_value = "<dummy>XML</dummy>"
        mock_parse.return_value = pd.DataFrame({
            'start_time': [pd.Timestamp('2022-01-01 00:00:00+00:00')],
            'end_time': [pd.Timestamp('2022-01-01 01:00:00+00:00')],
            'psr_type': ['B01'],
            'quantity': [100.0],
            'resolution': [pd.Timedelta('1 hour')]
        })

        start_date = datetime(2022, 1, 1)
        end_date = datetime(2022, 1, 2)
        result = self.fetcher.get_generation_data('10YPT-REN------W', start_date, end_date)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)
        mock_request.assert_called_once()
        mock_parse.assert_called_once_with("<dummy>XML</dummy>")

    @patch('src.data_fetcher.requests.get')
    def test_caching(self, mock_get):
        mock_response = Mock()
        mock_response.text = """
        <GL_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0">
          <TimeSeries>
            <MktPSRType>
              <psrType>B01</psrType>
            </MktPSRType>
            <Period>
              <timeInterval>
                <start>2022-01-01T00:00:00</start>
                <end>2022-01-02T00:00:00</end>
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
        result1 = self.fetcher.get_generation_data('10YPT-REN------W', start_date, end_date)
        self.assertIsInstance(result1, pd.DataFrame)
        self.assertFalse(result1.empty)
        mock_get.assert_called_once()

        # Print debug information
        print("Result 1:")
        print(result1)
        print("Cache contents after first call:")
        print(os.listdir(self.fetcher.CACHE_DIR))

        # Reset the mock
        mock_get.reset_mock()

        # Second call with the same parameters should use cached data
        result2 = self.fetcher.get_generation_data('10YPT-REN------W', start_date, end_date)
        self.assertIsInstance(result2, pd.DataFrame)
        
        # Print debug information
        print("Result 2:")
        print(result2)
        
        self.assertFalse(result2.empty)
        mock_get.assert_not_called()  # The mock should not be called for the second request

        # Check if the results are the same
        pd.testing.assert_frame_equal(result1, result2)

        # Print cache key and contents
        params = {
            'documentType': 'A75',
            'processType': 'A16',
            'in_Domain': '10YPT-REN------W',
            'outBiddingZone_Domain': '10YPT-REN------W',
        }
        cache_key = self.fetcher._get_cache_key(params)
        print(f"Cache key: {cache_key}")
        print("Cache file contents:")
        cache_file = os.path.join(self.fetcher.CACHE_DIR, f"{cache_key}.parquet")
        if os.path.exists(cache_file):
            print(pd.read_parquet(cache_file))
        else:
            print("Cache file not found")

        # Third call with a different date range that overlaps should make a new request
        new_start_date = datetime(2022, 1, 1, 12)
        new_end_date = datetime(2022, 1, 2, 12)
        result3 = self.fetcher.get_generation_data('10YPT-REN------W', new_start_date, new_end_date)
        self.assertIsInstance(result3, pd.DataFrame)
        self.assertFalse(result3.empty)
        mock_get.assert_called_once()  # The mock should be called for the third request

    @patch('src.data_fetcher.requests.get')
    def test_caching_different_params(self, mock_get):
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

    def test_cache_file_creation(self):
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

    @patch('src.data_fetcher.requests.get')
    def test_edge_case_date_ranges(self, mock_get):
        def mock_response(start_date, end_date):
            # If start_date and end_date are the same, use end_date + 1 hour
            if start_date == end_date:
                end_date = start_date + timedelta(hours=1)
            
            return f"""
            <GL_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0">
              <TimeSeries>
                <MktPSRType>
                  <psrType>B01</psrType>
                </MktPSRType>
                <Period>
                  <timeInterval>
                    <start>{start_date.strftime('%Y-%m-%dT%H:%MZ')}</start>
                    <end>{end_date.strftime('%Y-%m-%dT%H:%MZ')}</end>
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

        mock_response_obj = Mock()
        mock_response_obj.raise_for_status.return_value = None
        mock_get.return_value = mock_response_obj

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
            mock_response_obj.text = mock_response(start_date, end_date)
            result = self.fetcher.get_generation_data('10YPT-REN------W', start_date, end_date)
            self.assertIsInstance(result, pd.DataFrame)
            self.assertFalse(result.empty, f"Empty result for date range: {start_date} to {end_date}")
            self.assertTrue(all(result['start_time'].between(start_date, end_date - timedelta(seconds=1))))

    @patch('src.data_fetcher.requests.get')
    def test_portugal_generation_data(self, mock_get):
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
        
        # Check if the result matches the expected data in the file
        self.assertFalse(result.empty, "Expected non-empty result")
        self.assertEqual(result['start_time'].min(), pd.Timestamp('2024-01-01 00:00:00+00:00'))
        self.assertLess(result['start_time'].max(), pd.Timestamp('2024-01-01 03:00:00+00:00'))
        
        # Check if all expected PSR types are present
        expected_psr_types = {'B01', 'B04', 'B05', 'B10', 'B11', 'B12', 'B16', 'B18', 'B19', 'B20'}
        actual_psr_types = set(result['psr_type'].unique())
        self.assertEqual(actual_psr_types, expected_psr_types, 
                         f"Mismatch in PSR types. Expected: {expected_psr_types}, Actual: {actual_psr_types}")
        
        # Check if the resolution is correct
        self.assertTrue(all(result['resolution'] == pd.Timedelta('1 hour')), "Resolution should be 1 hour for all entries")

    def test_spain_generation_data(self):
        start_date = datetime(2024, 1, 1, 0, 0)
        end_date = datetime(2024, 1, 1, 2, 0)
        
        fetcher = ENTSOEDataFetcher(API_TOKEN)
        result = fetcher.get_generation_data('10YES-REE------0', start_date, end_date)

        values = [5632, 5664, 5672, 5656, 5608, 5612, 5544, 5448]
        averages = [sum(values[i:i+4]) / 4 for i in range(0, len(values), 4)]
        
        print("Averages for each set of 4 values:", averages)

        print(result)
        

if __name__ == '__main__':
    unittest.main()

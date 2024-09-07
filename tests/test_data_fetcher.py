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
                <start>2023-01-01T00:00Z</start>
                <end>2023-01-01T03:00Z</end>
              </timeInterval>
              <resolution>PT60M</resolution>
              <Point>
                <position>1</position>
                <quantity>1000</quantity>
              </Point>
              <Point>
                <position>2</position>
                <quantity>1100</quantity>
              </Point>
              <Point>
                <position>3</position>
                <quantity>1200</quantity>
              </Point>
            </Period>
          </TimeSeries>
        </GL_MarketDocument>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        start_date = datetime(2023, 1, 1, 0, 0)
        end_date = datetime(2023, 1, 1, 3, 0)
        
        result = self.fetcher.get_generation_data('10YPT-REN------W', start_date, end_date)
        
        print("\nPortugal Generation Data for the first 3 hours of 2023:")
        print(result)
        
        logger.debug("test_portugal_generation_data completed")

if __name__ == '__main__':
    unittest.main()

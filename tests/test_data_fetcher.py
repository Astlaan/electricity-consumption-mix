import unittest
from unittest.mock import patch, Mock
from datetime import datetime
import pandas as pd
from src.data_fetcher import ENTSOEDataFetcher

class TestENTSOEDataFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = ENTSOEDataFetcher("dummy_token")

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
        mock_parse.return_value = pd.DataFrame({'dummy': [1, 2, 3]})

        start_date = datetime(2022, 1, 1)
        end_date = datetime(2022, 1, 2)
        result = self.fetcher.get_generation_data('10YPT-REN------W', start_date, end_date)

        self.assertIsInstance(result, pd.DataFrame)
        mock_request.assert_called_once()
        mock_parse.assert_called_once_with("<dummy>XML</dummy>")

if __name__ == '__main__':
    unittest.main()

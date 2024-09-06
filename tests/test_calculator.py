import unittest
import pandas as pd
from src.calculator import ElectricityMixCalculator

class TestElectricityMixCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = ElectricityMixCalculator()

    def test_calculate_mix(self):
        # Create sample data
        pt_data = {
            'generation': pd.DataFrame({'solar': [100, 200], 'wind': [300, 400]}),
            'imports': pd.Series([50, 60]),
            'exports': pd.Series([10, 20])
        }
        es_data = {
            'generation': pd.DataFrame({'solar': [500, 600], 'wind': [700, 800]}),
            'imports_fr': pd.Series([100, 110]),
            'exports_fr': pd.Series([30, 40])
        }
        fr_data = {
            'generation': pd.DataFrame({'solar': [200, 300], 'wind': [400, 500]})
        }

        # Test without French contribution
        result_without_france = self.calculator.calculate_mix(pt_data, es_data, None, False)
        self.assertIsInstance(result_without_france, pd.DataFrame)
        self.assertEqual(result_without_france.shape, (2, 2))

        # Test with French contribution
        result_with_france = self.calculator.calculate_mix(pt_data, es_data, fr_data, True)
        self.assertIsInstance(result_with_france, pd.DataFrame)
        self.assertEqual(result_with_france.shape, (2, 2))

if __name__ == '__main__':
    unittest.main()

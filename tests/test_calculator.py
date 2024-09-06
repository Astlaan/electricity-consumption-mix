import unittest
import pandas as pd
from src.calculator import ElectricityMixCalculator

class TestElectricityMixCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = ElectricityMixCalculator()

    def test_calculate_mix(self):
        # Create sample data
        pt_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z'],
                'psr_type': ['B16', 'B16'],
                'quantity': [100, 200]
            }),
            'imports': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z'],
                'quantity': [50, 60]
            }),
            'exports': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z'],
                'quantity': [10, 20]
            })
        }
        es_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z'],
                'psr_type': ['B16', 'B16'],
                'quantity': [500, 600]
            }),
            'imports_fr': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z'],
                'quantity': [100, 110]
            }),
            'exports_fr': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z'],
                'quantity': [30, 40]
            })
        }
        fr_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z'],
                'psr_type': ['B16', 'B16'],
                'quantity': [200, 300]
            })
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

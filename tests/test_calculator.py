import unittest
import pandas as pd
import sys
from pathlib import Path

# Add the project root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

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
import unittest
import pandas as pd
from src.calculator import ElectricityMixCalculator

class TestElectricityMixCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = ElectricityMixCalculator()

    def test_calculate_mix_normal_case(self):
        pt_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z'],
                'psr_type': ['B01', 'B02'],
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
                'psr_type': ['B01', 'B02'],
                'quantity': [500, 600]
            })
        }

        result = self.calculator.calculate_mix(pt_data, es_data)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, (2, 2))
        self.assertTrue((result.sum(axis=1) - 100).abs().max() < 1e-6)  # Sum should be close to 100%

    def test_calculate_mix_zero_imports_exports(self):
        pt_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T00:00:00Z'],
                'psr_type': ['B01', 'B02'],
                'quantity': [100, 200]
            }),
            'imports': pd.DataFrame({'start_time': ['2023-05-01T00:00:00Z'], 'quantity': [0]}),
            'exports': pd.DataFrame({'start_time': ['2023-05-01T00:00:00Z'], 'quantity': [0]})
        }
        es_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T00:00:00Z'],
                'psr_type': ['B01', 'B02'],
                'quantity': [500, 500]
            })
        }

        result = self.calculator.calculate_mix(pt_data, es_data)
        expected = pd.DataFrame({'B01': [33.33], 'B02': [66.67]}, index=pd.to_datetime(['2023-05-01T00:00:00Z']))
        pd.testing.assert_frame_equal(result, expected, atol=0.01)

    def test_calculate_mix_negative_net_imports(self):
        pt_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T00:00:00Z'],
                'psr_type': ['B01', 'B02'],
                'quantity': [100, 200]
            }),
            'imports': pd.DataFrame({'start_time': ['2023-05-01T00:00:00Z'], 'quantity': [10]}),
            'exports': pd.DataFrame({'start_time': ['2023-05-01T00:00:00Z'], 'quantity': [50]})
        }
        es_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T00:00:00Z'],
                'psr_type': ['B01', 'B02'],
                'quantity': [500, 500]
            })
        }

        result = self.calculator.calculate_mix(pt_data, es_data)
        self.assertTrue((result >= 0).all().all())  # All percentages should be non-negative
        self.assertTrue((result.sum(axis=1) - 100).abs().max() < 1e-6)  # Sum should be close to 100%

    def test_calculate_mix_mismatched_sources(self):
        pt_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T00:00:00Z'],
                'psr_type': ['B01', 'B02'],
                'quantity': [100, 200]
            }),
            'imports': pd.DataFrame({'start_time': ['2023-05-01T00:00:00Z'], 'quantity': [50]}),
            'exports': pd.DataFrame({'start_time': ['2023-05-01T00:00:00Z'], 'quantity': [10]})
        }
        es_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T00:00:00Z'],
                'psr_type': ['B03', 'B04'],
                'quantity': [500, 500]
            })
        }

        result = self.calculator.calculate_mix(pt_data, es_data)
        self.assertEqual(set(result.columns), {'B01', 'B02', 'B03', 'B04'})
        self.assertTrue((result.sum(axis=1) - 100).abs().max() < 1e-6)  # Sum should be close to 100%

    def test_calculate_mix_empty_data(self):
        pt_data = {
            'generation': pd.DataFrame(),
            'imports': pd.DataFrame(),
            'exports': pd.DataFrame()
        }
        es_data = {
            'generation': pd.DataFrame()
        }

        result = self.calculator.calculate_mix(pt_data, es_data)
        self.assertTrue(result.empty)

    def test_calculate_mix_single_source(self):
        pt_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z'],
                'psr_type': ['B01'],
                'quantity': [100]
            }),
            'imports': pd.DataFrame({'start_time': ['2023-05-01T00:00:00Z'], 'quantity': [0]}),
            'exports': pd.DataFrame({'start_time': ['2023-05-01T00:00:00Z'], 'quantity': [0]})
        }
        es_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z'],
                'psr_type': ['B01'],
                'quantity': [500]
            })
        }

        result = self.calculator.calculate_mix(pt_data, es_data)
        expected = pd.DataFrame({'B01': [100.0]}, index=pd.to_datetime(['2023-05-01T00:00:00Z']))
        pd.testing.assert_frame_equal(result, expected)

    def test_calculate_mix_multiple_timestamps(self):
        pt_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z', '2023-05-01T02:00:00Z'],
                'psr_type': ['B01', 'B01', 'B01'],
                'quantity': [100, 150, 200]
            }),
            'imports': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z', '2023-05-01T02:00:00Z'],
                'quantity': [50, 60, 70]
            }),
            'exports': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z', '2023-05-01T02:00:00Z'],
                'quantity': [10, 20, 30]
            })
        }
        es_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z', '2023-05-01T02:00:00Z'],
                'psr_type': ['B01', 'B01', 'B01'],
                'quantity': [500, 600, 700]
            })
        }

        result = self.calculator.calculate_mix(pt_data, es_data)
        self.assertEqual(result.shape, (3, 1))
        self.assertTrue((result.sum(axis=1) - 100).abs().max() < 1e-6)  # Sum should be close to 100%

if __name__ == '__main__':
    unittest.main()

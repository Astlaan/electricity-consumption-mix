import unittest
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from src.calculator import ElectricityMixCalculator
from src.utils import PSR_TYPE_MAPPING

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

    def test_calculate_mix_with_empty_data(self):
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

    def test_calculate_mix_with_missing_data(self):
        pt_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z'],
                'psr_type': ['B01'],
                'quantity': [100]
            })
            # Missing 'imports' and 'exports'
        }
        es_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z'],
                'psr_type': ['B01'],
                'quantity': [500]
            })
        }
        result = self.calculator.calculate_mix(pt_data, es_data)
        self.assertFalse(result.empty)
        self.assertEqual(result.shape, (1, 1))

    def test_calculate_mix_with_different_energy_sources(self):
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
                'quantity': [300, 400]
            })
        }
        result = self.calculator.calculate_mix(pt_data, es_data)
        self.assertEqual(set(result.columns), {'B01', 'B02', 'B03', 'B04'})
        self.assertTrue((result.sum(axis=1) - 100).abs().max() < 1e-6)  # Sum should be close to 100%

if __name__ == '__main__':
    unittest.main()
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from src.calculator import ElectricityMixCalculator
from src.utils import PSR_TYPE_MAPPING

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
        expected.index.name = None
        expected.columns.name = None
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
        expected.index.name = None
        expected.columns.name = None
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

    def test_calculate_mix_large_dataset(self):
        # Generate a large dataset spanning a year
        dates = pd.date_range(start='2022-01-01', end='2022-12-31', freq='H')
        pt_data = {
            'generation': pd.DataFrame({
                'start_time': dates.repeat(2),
                'psr_type': ['B01', 'B02'] * len(dates),
                'quantity': np.random.rand(len(dates) * 2) * 1000
            }),
            'imports': pd.DataFrame({
                'start_time': dates,
                'quantity': np.random.rand(len(dates)) * 100
            }),
            'exports': pd.DataFrame({
                'start_time': dates,
                'quantity': np.random.rand(len(dates)) * 100
            })
        }
        es_data = {
            'generation': pd.DataFrame({
                'start_time': dates.repeat(2),
                'psr_type': ['B01', 'B02'] * len(dates),
                'quantity': np.random.rand(len(dates) * 2) * 1000
            })
        }

        result = self.calculator.calculate_mix(pt_data, es_data)
        
        self.assertEqual(len(result), len(dates))  # Should have one row per hour
        self.assertEqual(set(result.columns), {'B01', 'B02'})  # Should have both energy types
        self.assertTrue((result.sum(axis=1) - 100).abs().max() < 1e-6)  # Sum should always be close to 100%

    def test_calculate_mix_missing_data(self):
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        dates = pd.date_range(start='2023-05-01', end='2023-05-03', freq='H')
        pt_data = {
            'generation': pd.DataFrame({
                'start_time': dates.repeat(2),
                'psr_type': ['B01', 'B02'] * len(dates),
                'quantity': np.random.rand(len(dates) * 2) * 1000
            }),
            'imports': pd.DataFrame({
                'start_time': dates,
                'quantity': np.random.rand(len(dates)) * 100
            }),
            'exports': pd.DataFrame({
                'start_time': dates,
                'quantity': np.random.rand(len(dates)) * 100
            })
        }
        es_data = {
            'generation': pd.DataFrame({
                'start_time': dates.repeat(2),
                'psr_type': ['B01', 'B02'] * len(dates),
                'quantity': np.random.rand(len(dates) * 2) * 1000
            })
        }

        # Remove some data points
        pt_data['generation'] = pt_data['generation'].sample(frac=0.8)
        es_data['generation'] = es_data['generation'].sample(frac=0.8)

        logger.debug(f"Input data shapes: pt_gen={pt_data['generation'].shape}, pt_imports={pt_data['imports'].shape}, pt_exports={pt_data['exports'].shape}, es_gen={es_data['generation'].shape}")

        result = self.calculator.calculate_mix(pt_data, es_data)
        
        logger.debug(f"Result shape: {result.shape}")
        logger.debug(f"Result sum: {result.sum(axis=1)}")
        logger.debug(f"Max difference from 100: {(result.sum(axis=1) - 100).abs().max()}")
        
        self.assertLessEqual(len(result), len(dates))  # Should have fewer rows due to missing data
        self.assertTrue((result.sum(axis=1) - 100).abs().max() < 1e-6)  # Sum should always be close to 100%

    def test_calculate_mix_extreme_values(self):
        pt_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z'],
                'psr_type': ['B01', 'B02'],
                'quantity': [1e10, 1e-10]  # Extremely large and small values
            }),
            'imports': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z'],
                'quantity': [1e8, 1e-8]
            }),
            'exports': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z'],
                'quantity': [1e7, 1e-7]
            })
        }
        es_data = {
            'generation': pd.DataFrame({
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z'],
                'psr_type': ['B01', 'B02'],
                'quantity': [1e9, 1e-9]
            })
        }

        result = self.calculator.calculate_mix(pt_data, es_data)
        self.assertTrue((result >= 0).all().all())  # All percentages should be non-negative
        self.assertTrue((result.sum(axis=1) - 100).abs().max() < 1e-6)  # Sum should be close to 100%

    def test_calculate_mix_daylight_saving(self):
        # Test with data spanning a daylight saving time change
        start_date = datetime(2023, 3, 25)  # Before DST change
        end_date = datetime(2023, 3, 27)  # After DST change
        dates = pd.date_range(start=start_date, end=end_date, freq='H')
        
        pt_data = {
            'generation': pd.DataFrame({
                'start_time': dates.repeat(2),
                'psr_type': ['B01', 'B02'] * len(dates),
                'quantity': np.random.rand(len(dates) * 2) * 1000
            }),
            'imports': pd.DataFrame({
                'start_time': dates,
                'quantity': np.random.rand(len(dates)) * 100
            }),
            'exports': pd.DataFrame({
                'start_time': dates,
                'quantity': np.random.rand(len(dates)) * 100
            })
        }
        es_data = {
            'generation': pd.DataFrame({
                'start_time': dates.repeat(2),
                'psr_type': ['B01', 'B02'] * len(dates),
                'quantity': np.random.rand(len(dates) * 2) * 1000
            })
        }

        result = self.calculator.calculate_mix(pt_data, es_data)
        self.assertEqual(len(result), len(dates))
        self.assertTrue((result.sum(axis=1) - 100).abs().max() < 1e-6)  # Sum should be close to 100%

    def test_calculate_mix_data_inconsistency(self):
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
            }),
            'exports': pd.DataFrame({  # This doesn't match Portugal's imports
                'start_time': ['2023-05-01T00:00:00Z', '2023-05-01T01:00:00Z'],
                'quantity': [100, 120]  # Different from Portugal's imports
            })
        }

        result = self.calculator.calculate_mix(pt_data, es_data)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue((result.sum(axis=1) - 100).abs().max() < 1e-6)  # Sum should still be close to 100%

    def test_calculate_mix_all_psr_types(self):
        dates = pd.date_range(start='2023-05-01', end='2023-05-02', freq='H')
        psr_types = list(PSR_TYPE_MAPPING.keys())
        
        pt_data = {
            'generation': pd.DataFrame({
                'start_time': dates.repeat(len(psr_types)),
                'psr_type': psr_types * len(dates),
                'quantity': np.random.rand(len(dates) * len(psr_types)) * 1000
            }),
            'imports': pd.DataFrame({
                'start_time': dates,
                'quantity': np.random.rand(len(dates)) * 100
            }),
            'exports': pd.DataFrame({
                'start_time': dates,
                'quantity': np.random.rand(len(dates)) * 100
            })
        }
        es_data = {
            'generation': pd.DataFrame({
                'start_time': dates.repeat(len(psr_types)),
                'psr_type': psr_types * len(dates),
                'quantity': np.random.rand(len(dates) * len(psr_types)) * 1000
            })
        }

        result = self.calculator.calculate_mix(pt_data, es_data)
        self.assertEqual(set(result.columns), set(psr_types))
        self.assertTrue((result.sum(axis=1) - 100).abs().max() < 1e-6)  # Sum should be close to 100%

if __name__ == '__main__':
    unittest.main()

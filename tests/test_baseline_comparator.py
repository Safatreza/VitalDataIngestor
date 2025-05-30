import unittest
from datetime import datetime
import json
import os
from baseline_comparator import BaselineComparator, AlertSeverity

class TestBaselineComparator(unittest.TestCase):
    def setUp(self):
        """Set up test data and comparator."""
        self.comparator = BaselineComparator()
        
        # Create test baseline data
        self.test_baselines = {
            "heart_rate": {
                "adult": {
                    "M": {
                        "min": 60,
                        "max": 100,
                        "severity_threshold": 20.0
                    },
                    "F": {
                        "min": 60,
                        "max": 100,
                        "severity_threshold": 20.0
                    }
                }
            },
            "temperature": {
                "adult": {
                    "M": {
                        "min": 36.5,
                        "max": 37.5,
                        "severity_threshold": 10.0
                    },
                    "F": {
                        "min": 36.5,
                        "max": 37.5,
                        "severity_threshold": 10.0
                    }
                }
            }
        }
        
        # Save test baselines to a temporary JSON file
        self.test_json_path = "test_baselines.json"
        with open(self.test_json_path, 'w') as f:
            json.dump(self.test_baselines, f)
        
        # Load the test baselines
        self.comparator.load_baselines_from_json(self.test_json_path)
    
    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.test_json_path):
            os.remove(self.test_json_path)
    
    def test_age_group_calculation(self):
        """Test age group calculation."""
        # Test infant
        dob = datetime.now()
        self.assertEqual(self.comparator._get_age_group(0), "infant")
        
        # Test child
        self.assertEqual(self.comparator._get_age_group(5), "child")
        
        # Test adolescent
        self.assertEqual(self.comparator._get_age_group(15), "adolescent")
        
        # Test adult
        self.assertEqual(self.comparator._get_age_group(30), "adult")
        
        # Test elderly
        self.assertEqual(self.comparator._get_age_group(70), "elderly")
    
    def test_baseline_comparison(self):
        """Test vital signs comparison against baselines."""
        # Test normal values
        vital_signs = {
            "heart_rate": 75,
            "temperature": 37.0
        }
        dob = datetime(1990, 1, 1)
        
        alerts = self.comparator.compare_vital_signs(vital_signs, dob, "M")
        self.assertEqual(len(alerts), 2)
        self.assertTrue(all(alert.severity == AlertSeverity.INFO for alert in alerts))
        
        # Test warning values
        vital_signs = {
            "heart_rate": 110,  # Slightly above normal
            "temperature": 37.0
        }
        
        alerts = self.comparator.compare_vital_signs(vital_signs, dob, "M")
        heart_rate_alert = next(alert for alert in alerts if alert.vital_sign == "heart_rate")
        self.assertEqual(heart_rate_alert.severity, AlertSeverity.WARNING)
        
        # Test critical values
        vital_signs = {
            "heart_rate": 150,  # Well above normal
            "temperature": 37.0
        }
        
        alerts = self.comparator.compare_vital_signs(vital_signs, dob, "M")
        heart_rate_alert = next(alert for alert in alerts if alert.vital_sign == "heart_rate")
        self.assertEqual(heart_rate_alert.severity, AlertSeverity.CRITICAL)
    
    def test_baseline_range_retrieval(self):
        """Test retrieving baseline ranges."""
        baseline = self.comparator.get_baseline_range("heart_rate", "adult", "M")
        self.assertIsNotNone(baseline)
        self.assertEqual(baseline.min_value, 60)
        self.assertEqual(baseline.max_value, 100)
        
        # Test non-existent range
        baseline = self.comparator.get_baseline_range("heart_rate", "infant", "M")
        self.assertIsNone(baseline)
    
    def test_json_loading(self):
        """Test loading baselines from JSON file."""
        # Create a new comparator and load the test baselines
        comparator = BaselineComparator()
        comparator.load_baselines_from_json(self.test_json_path)
        
        # Verify the loaded data
        baseline = comparator.get_baseline_range("heart_rate", "adult", "M")
        self.assertIsNotNone(baseline)
        self.assertEqual(baseline.min_value, 60)
        self.assertEqual(baseline.max_value, 100)
        self.assertEqual(baseline.severity_threshold, 20.0)

if __name__ == '__main__':
    unittest.main() 
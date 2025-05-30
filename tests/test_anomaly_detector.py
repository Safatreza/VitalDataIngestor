import unittest
from datetime import datetime
import os
from anomaly_detector import AnomalyDetector, AnomalyPrediction

class TestAnomalyDetector(unittest.TestCase):
    def setUp(self):
        """Set up test data and detector."""
        self.detector = AnomalyDetector(model_path="test_model.joblib")
        
        # Normal vital signs
        self.normal_vitals = {
            'heart_rate': 75,
            'temperature': 37.0,
            'spo2': 98,
            'respiratory_rate': 16,
            'systolic_bp': 120,
            'diastolic_bp': 80
        }
        
        # Abnormal vital signs
        self.abnormal_vitals = {
            'heart_rate': 150,
            'temperature': 39.0,
            'spo2': 92,
            'respiratory_rate': 28,
            'systolic_bp': 180,
            'diastolic_bp': 110
        }
    
    def tearDown(self):
        """Clean up test files."""
        if os.path.exists("test_model.joblib"):
            os.remove("test_model.joblib")
    
    def test_model_training(self):
        """Test model training and evaluation."""
        self.detector.train_model(n_samples=100)
        self.assertIsNotNone(self.detector.model)
        self.assertIsNotNone(self.detector.scaler)
    
    def test_normal_prediction(self):
        """Test prediction on normal vital signs."""
        self.detector.train_model(n_samples=100)
        prediction = self.detector.predict(self.normal_vitals, datetime.now())
        
        self.assertIsInstance(prediction, AnomalyPrediction)
        self.assertFalse(prediction.is_anomaly)
        self.assertLess(prediction.confidence, 0.5)
        self.assertEqual(prediction.vital_signs, self.normal_vitals)
    
    def test_abnormal_prediction(self):
        """Test prediction on abnormal vital signs."""
        self.detector.train_model(n_samples=100)
        prediction = self.detector.predict(self.abnormal_vitals, datetime.now())
        
        self.assertIsInstance(prediction, AnomalyPrediction)
        self.assertTrue(prediction.is_anomaly)
        self.assertGreater(prediction.confidence, 0.5)
        self.assertEqual(prediction.vital_signs, self.abnormal_vitals)
    
    def test_model_saving_loading(self):
        """Test saving and loading the model."""
        # Train and save model
        self.detector.train_model(n_samples=100)
        self.detector.save_model()
        
        # Create new detector and load model
        new_detector = AnomalyDetector(model_path="test_model.joblib")
        
        # Compare predictions
        original_pred = self.detector.predict(self.normal_vitals, datetime.now())
        loaded_pred = new_detector.predict(self.normal_vitals, datetime.now())
        
        self.assertEqual(original_pred.is_anomaly, loaded_pred.is_anomaly)
        self.assertAlmostEqual(original_pred.confidence, loaded_pred.confidence)
    
    def test_anomaly_details(self):
        """Test individual vital sign anomaly scores."""
        self.detector.train_model(n_samples=100)
        prediction = self.detector.predict(self.abnormal_vitals, datetime.now())
        
        self.assertIsInstance(prediction.details, dict)
        self.assertEqual(len(prediction.details), 6)  # One score per vital sign
        
        # Check that abnormal vital signs have higher scores
        for vital_sign, score in prediction.details.items():
            self.assertGreater(score, 0)  # All scores should be positive
            if vital_sign in self.abnormal_vitals:
                self.assertGreater(score, 1.0)  # Abnormal values should have high z-scores

if __name__ == '__main__':
    unittest.main() 
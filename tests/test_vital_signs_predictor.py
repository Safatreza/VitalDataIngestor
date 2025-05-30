import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.analysis.vital_signs_predictor import VitalSignsPredictor
from src.utils.mock_data_generator import MockDataGenerator

class TestVitalSignsPredictor(unittest.TestCase):
    """Test cases for the VitalSignsPredictor class."""
    
    def setUp(self):
        """Set up test data."""
        # Generate mock data
        generator = MockDataGenerator()
        generator.generate_dataset(
            num_patients=2,
            start_time=datetime.now() - timedelta(days=10),
            duration_hours=240,  # 10 days
            output_file='test_data.csv'
        )
        
        # Load the data
        self.data = pd.read_csv('test_data.csv')
        
        # Initialize predictor
        self.predictor = VitalSignsPredictor(model_path='test_model.h5')
    
    def tearDown(self):
        """Clean up test files."""
        import os
        if os.path.exists('test_data.csv'):
            os.remove('test_data.csv')
        if os.path.exists('test_model.h5'):
            os.remove('test_model.h5')
        if os.path.exists('training_history.png'):
            os.remove('training_history.png')
        if os.path.exists('predictions.png'):
            os.remove('predictions.png')
    
    def test_preprocessing(self):
        """Test data preprocessing."""
        X, y = self.predictor._preprocess_data(self.data)
        
        # Check shapes
        self.assertEqual(len(X.shape), 3)  # (samples, sequence_length, features)
        self.assertEqual(X.shape[1], self.predictor.sequence_length)
        self.assertEqual(X.shape[2], len(self.predictor.vital_signs))
        
        # Check that X and y have the same number of samples
        self.assertEqual(len(X), len(y))
        
        # Check that y has the correct number of features
        self.assertEqual(y.shape[1], len(self.predictor.vital_signs))
    
    def test_model_building(self):
        """Test model building."""
        X, _ = self.predictor._preprocess_data(self.data)
        model = self.predictor._build_model(input_shape=(X.shape[1], X.shape[2]))
        
        # Check model architecture
        self.assertEqual(len(model.layers), 5)  # 2 LSTM, 2 Dense, 1 Dropout
        self.assertEqual(model.layers[-1].output_shape[-1], len(self.predictor.vital_signs))
    
    def test_training(self):
        """Test model training."""
        # Train the model
        self.predictor.train('test_data.csv', validation_split=0.2)
        
        # Check that model was created
        self.assertIsNotNone(self.predictor.model)
        
        # Check that scalers were created
        self.assertEqual(len(self.predictor.scalers), len(self.predictor.vital_signs))
    
    def test_prediction(self):
        """Test making predictions."""
        # Train the model first
        self.predictor.train('test_data.csv', validation_split=0.2)
        
        # Get data for a single patient
        patient_id = self.data['patient_id'].iloc[0]
        patient_data = self.data[self.data['patient_id'] == patient_id]
        
        # Make prediction
        prediction = self.predictor.predict_next_day(patient_data)
        
        # Check prediction format
        self.assertIsInstance(prediction, dict)
        self.assertEqual(len(prediction), len(self.predictor.vital_signs))
        
        # Check that all vital signs are present
        for vital_sign in self.predictor.vital_signs:
            self.assertIn(vital_sign, prediction)
            self.assertIsInstance(prediction[vital_sign], float)
    
    def test_plotting(self):
        """Test plotting functionality."""
        # Train the model first
        self.predictor.train('test_data.csv', validation_split=0.2)
        
        # Get data for a single patient
        patient_id = self.data['patient_id'].iloc[0]
        patient_data = self.data[self.data['patient_id'] == patient_id]
        
        # Generate plots
        self.predictor.plot_predictions(patient_data, days_to_plot=7)
        
        # Check that plot file was created
        import os
        self.assertTrue(os.path.exists('predictions.png'))

if __name__ == '__main__':
    unittest.main() 
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
import logging

@dataclass
class AnomalyPrediction:
    """Data class to hold anomaly prediction results."""
    is_anomaly: bool
    confidence: float
    vital_signs: Dict[str, float]
    timestamp: datetime
    details: Dict[str, float]

class AnomalyDetector:
    """Machine learning-based anomaly detection for vital signs."""
    
    def __init__(self, model_path: str = "anomaly_model.joblib"):
        """Initialize the anomaly detector."""
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        
        # Try to load existing model
        try:
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(f"{model_path}.scaler")
        except FileNotFoundError:
            logging.error(f"No existing model found at {model_path}")
    
    def _generate_mock_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """Generate mock training data with normal and abnormal patterns."""
        data = []
        
        # Generate normal data
        n_normal = int(n_samples * 0.8)
        for _ in range(n_normal):
            data.append({
                'heart_rate': np.random.normal(75, 10),
                'temperature': np.random.normal(37.0, 0.5),
                'spo2': np.random.normal(98, 1),
                'respiratory_rate': np.random.normal(16, 2),
                'systolic_bp': np.random.normal(120, 10),
                'diastolic_bp': np.random.normal(80, 5),
                'is_anomaly': 0
            })
        
        # Generate abnormal data
        n_abnormal = n_samples - n_normal
        for _ in range(n_abnormal):
            # Randomly choose an abnormal pattern
            pattern = np.random.choice(['fever', 'hypotension', 'respiratory_distress'])
            
            if pattern == 'fever':
                data.append({
                    'heart_rate': np.random.normal(100, 15),
                    'temperature': np.random.normal(39.0, 0.3),
                    'spo2': np.random.normal(95, 2),
                    'respiratory_rate': np.random.normal(20, 3),
                    'systolic_bp': np.random.normal(130, 15),
                    'diastolic_bp': np.random.normal(85, 8),
                    'is_anomaly': 1
                })
            elif pattern == 'hypotension':
                data.append({
                    'heart_rate': np.random.normal(90, 10),
                    'temperature': np.random.normal(36.5, 0.5),
                    'spo2': np.random.normal(97, 1),
                    'respiratory_rate': np.random.normal(18, 2),
                    'systolic_bp': np.random.normal(90, 5),
                    'diastolic_bp': np.random.normal(60, 5),
                    'is_anomaly': 1
                })
            else:  # respiratory_distress
                data.append({
                    'heart_rate': np.random.normal(110, 15),
                    'temperature': np.random.normal(37.2, 0.4),
                    'spo2': np.random.normal(92, 2),
                    'respiratory_rate': np.random.normal(25, 3),
                    'systolic_bp': np.random.normal(140, 15),
                    'diastolic_bp': np.random.normal(90, 8),
                    'is_anomaly': 1
                })
        
        return pd.DataFrame(data)
    
    def _preprocess_data(self, vital_signs: Dict[str, float]) -> np.ndarray:
        """Preprocess vital signs data for model prediction."""
        # Convert to DataFrame for consistency
        df = pd.DataFrame([vital_signs])
        
        # Scale the features
        return self.scaler.transform(df)
    
    def train_model(self, n_samples: int = 1000) -> None:
        """Train the anomaly detection model on mock data."""
        # Generate training data
        data = self._generate_mock_data(n_samples)
        
        # Prepare features and target
        X = data.drop('is_anomaly', axis=1)
        y = data['is_anomaly']
        
        # Scale the features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train the model
        self.model = LogisticRegression(random_state=42)
        self.model.fit(X_scaled, y)
        
        # Evaluate the model
        y_pred = self.model.predict(X_scaled)
        logging.info("\nModel Evaluation:")
        logging.info(classification_report(y, y_pred))
        logging.info("\nConfusion Matrix:")
        logging.info(confusion_matrix(y, y_pred))
        
        # Save the model and scaler
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, f"{self.model_path}.scaler")
    
    def predict(self, vital_signs: Dict[str, float], timestamp: datetime) -> AnomalyPrediction:
        """Make a prediction on new vital signs data."""
        if self.model is None:
            raise ValueError("Model not trained. Call train_model() first.")
        
        # Preprocess the data
        X = self._preprocess_data(vital_signs)
        
        # Make prediction
        is_anomaly = bool(self.model.predict(X)[0])
        confidence = float(self.model.predict_proba(X)[0][1])
        
        # Calculate individual anomaly scores using z-scores
        details = {}
        for vital_sign, value in vital_signs.items():
            mean = self.scaler.mean_[list(vital_signs.keys()).index(vital_sign)]
            std = np.sqrt(self.scaler.var_[list(vital_signs.keys()).index(vital_sign)])
            z_score = abs((value - mean) / std)
            details[vital_sign] = float(z_score)
        
        return AnomalyPrediction(
            is_anomaly=is_anomaly,
            confidence=confidence,
            vital_signs=vital_signs,
            timestamp=timestamp,
            details=details
        ) 
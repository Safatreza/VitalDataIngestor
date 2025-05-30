import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple, List, Dict, Optional
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

class VitalSignsPredictor:
    """LSTM-based predictor for vital signs."""
    
    def __init__(self, model_path: str = "vital_signs_model.h5"):
        """Initialize the predictor."""
        self.model_path = model_path
        self.model = None
        self.scalers: Dict[str, MinMaxScaler] = {}
        self.sequence_length = 7  # 7 days of data
        self.vital_signs = [
            'heart_rate', 'temperature', 'spo2',
            'respiratory_rate', 'systolic_bp', 'diastolic_bp'
        ]
        
        # Try to load existing model
        try:
            self.model = load_model(model_path)
            self._load_scalers()
        except:
            print(f"No existing model found at {model_path}")
    
    def _load_scalers(self) -> None:
        """Load saved scalers."""
        for vital_sign in self.vital_signs:
            scaler = MinMaxScaler()
            scaler_path = f"{self.model_path}.{vital_sign}.scaler"
            if os.path.exists(scaler_path):
                scaler.min_ = np.load(f"{scaler_path}.min.npy")
                scaler.scale_ = np.load(f"{scaler_path}.scale.npy")
                self.scalers[vital_sign] = scaler
    
    def _save_scalers(self) -> None:
        """Save scalers to disk."""
        for vital_sign, scaler in self.scalers.items():
            scaler_path = f"{self.model_path}.{vital_sign}.scaler"
            np.save(f"{scaler_path}.min.npy", scaler.min_)
            np.save(f"{scaler_path}.scale.npy", scaler.scale_)
    
    def _preprocess_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess the data for LSTM training."""
        # Sort by patient_id and timestamp
        df = df.sort_values(['patient_id', 'timestamp'])
        
        # Initialize scalers if not already loaded
        if not self.scalers:
            for vital_sign in self.vital_signs:
                self.scalers[vital_sign] = MinMaxScaler()
        
        # Normalize each vital sign
        normalized_data = {}
        for vital_sign in self.vital_signs:
            values = df[vital_sign].values.reshape(-1, 1)
            normalized_data[vital_sign] = self.scalers[vital_sign].fit_transform(values)
        
        # Create sequences
        X, y = [], []
        for patient_id in df['patient_id'].unique():
            patient_data = df[df['patient_id'] == patient_id]
            
            # Create sequences for each vital sign
            sequences = []
            for vital_sign in self.vital_signs:
                values = normalized_data[vital_sign][patient_data.index]
                for i in range(len(values) - self.sequence_length):
                    sequences.append(values[i:i + self.sequence_length])
            
            # Combine sequences
            for i in range(len(sequences[0])):
                sequence = np.column_stack([seq[i] for seq in sequences])
                X.append(sequence)
                
                # Target is the next day's values
                target = np.column_stack([
                    normalized_data[vital_sign][patient_data.index[i + self.sequence_length]]
                    for vital_sign in self.vital_signs
                ])
                y.append(target)
        
        return np.array(X), np.array(y)
    
    def _build_model(self, input_shape: Tuple[int, int]) -> Sequential:
        """Build the LSTM model."""
        model = Sequential([
            LSTM(64, input_shape=input_shape, return_sequences=True),
            Dropout(0.2),
            LSTM(32),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(len(self.vital_signs))
        ])
        
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def train(self, data_path: str, validation_split: float = 0.2) -> None:
        """Train the model on the provided data."""
        # Load and preprocess data
        df = pd.read_csv(data_path)
        X, y = self._preprocess_data(df)
        
        # Build and train model
        self.model = self._build_model(input_shape=(X.shape[1], X.shape[2]))
        
        # Callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            ModelCheckpoint(
                self.model_path,
                monitor='val_loss',
                save_best_only=True
            )
        ]
        
        # Train
        history = self.model.fit(
            X, y,
            validation_split=validation_split,
            epochs=100,
            batch_size=32,
            callbacks=callbacks,
            verbose=1
        )
        
        # Save scalers
        self._save_scalers()
        
        # Plot training history
        plt.figure(figsize=(12, 4))
        
        plt.subplot(1, 2, 1)
        plt.plot(history.history['loss'], label='Training Loss')
        plt.plot(history.history['val_loss'], label='Validation Loss')
        plt.title('Model Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        
        plt.subplot(1, 2, 2)
        plt.plot(history.history['mae'], label='Training MAE')
        plt.plot(history.history['val_mae'], label='Validation MAE')
        plt.title('Model MAE')
        plt.xlabel('Epoch')
        plt.ylabel('MAE')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig('training_history.png')
        plt.close()
    
    def predict_next_day(self, patient_data: pd.DataFrame) -> Dict[str, float]:
        """Predict the next day's vital signs for a patient."""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Ensure data is sorted by timestamp
        patient_data = patient_data.sort_values('timestamp')
        
        # Get the last 7 days of data
        last_week = patient_data.iloc[-self.sequence_length:]
        
        # Normalize the data
        normalized_sequence = []
        for vital_sign in self.vital_signs:
            values = last_week[vital_sign].values.reshape(-1, 1)
            normalized_values = self.scalers[vital_sign].transform(values)
            normalized_sequence.append(normalized_values)
        
        # Combine sequences
        X = np.column_stack(normalized_sequence)
        X = X.reshape(1, self.sequence_length, len(self.vital_signs))
        
        # Make prediction
        normalized_prediction = self.model.predict(X)[0]
        
        # Denormalize prediction
        prediction = {}
        for i, vital_sign in enumerate(self.vital_signs):
            value = normalized_prediction[i].reshape(-1, 1)
            prediction[vital_sign] = float(
                self.scalers[vital_sign].inverse_transform(value)[0][0]
            )
        
        return prediction
    
    def plot_predictions(
        self,
        patient_data: pd.DataFrame,
        days_to_plot: int = 7
    ) -> None:
        """Plot actual vs predicted values for a patient."""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Get the last n days of data
        recent_data = patient_data.sort_values('timestamp').iloc[-days_to_plot:]
        
        # Make predictions for each day
        predictions = []
        for i in range(len(recent_data) - self.sequence_length):
            sequence = recent_data.iloc[i:i + self.sequence_length]
            prediction = self.predict_next_day(sequence)
            predictions.append(prediction)
        
        # Create plots
        fig, axes = plt.subplots(3, 2, figsize=(15, 12))
        axes = axes.flatten()
        
        for i, vital_sign in enumerate(self.vital_signs):
            actual = recent_data[vital_sign].values[self.sequence_length:]
            predicted = [p[vital_sign] for p in predictions]
            
            ax = axes[i]
            ax.plot(actual, label='Actual', marker='o')
            ax.plot(predicted, label='Predicted', marker='x')
            ax.set_title(f'{vital_sign.replace("_", " ").title()}')
            ax.set_xlabel('Days')
            ax.set_ylabel('Value')
            ax.legend()
            ax.grid(True)
        
        plt.tight_layout()
        plt.savefig('predictions.png')
        plt.close() 
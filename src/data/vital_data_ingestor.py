import json
import csv
import time
import random
import os
from typing import Dict, List, Union, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests
from abc import ABC, abstractmethod
import logging

from src.data.models import VitalSigns
from src.data.data_sources import DataSource
from src.analysis.anomaly_detector import AnomalyDetector, AnomalyPrediction
from src.analysis.baseline_comparator import BaselineComparator, Alert

class DataSource(ABC):
    """Abstract base class for data sources."""
    @abstractmethod
    def get_data(self) -> List[VitalSigns]:
        """Retrieve and parse data from the source."""
        pass

class CSVDataSource(DataSource):
    """Data source for CSV files."""
    def __init__(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        self.file_path = file_path
        self._required_fields = {
            'heart_rate', 'temperature', 'spo2', 'respiratory_rate',
            'systolic_bp', 'diastolic_bp', 'timestamp', 'patient_id', 'age'
        }

    def get_data(self) -> List[VitalSigns]:
        vital_signs = []
        try:
            with open(self.file_path, 'r') as file:
                reader = csv.DictReader(file)
                
                # Validate required fields
                missing_fields = self._required_fields - set(reader.fieldnames)
                if missing_fields:
                    raise ValueError(f"Missing required fields in CSV: {missing_fields}")
                
                for row in reader:
                    try:
                        vital_signs.append(VitalSigns(
                            heart_rate=float(row['heart_rate']),
                            temperature=float(row['temperature']),
                            spo2=float(row['spo2']),
                            respiratory_rate=float(row['respiratory_rate']),
                            systolic_bp=float(row['systolic_bp']),
                            diastolic_bp=float(row['diastolic_bp']),
                            timestamp=datetime.fromisoformat(row['timestamp']),
                            patient_id=row['patient_id'],
                            age=int(row['age'])
                        ))
                    except (KeyError, ValueError) as e:
                        logging.error(f"Error processing row: {e}")
                        continue
                        
        except Exception as e:
            logging.error(f"Error reading CSV file: {e}")
            
        return vital_signs

class APIDataSource(DataSource):
    """Data source for JSON API endpoints."""
    def __init__(self, api_url: str, timeout: int = 10):
        self.api_url = api_url
        self.timeout = timeout
        self._required_fields = {
            'heart_rate', 'temperature', 'spo2', 'respiratory_rate',
            'systolic_bp', 'diastolic_bp', 'timestamp', 'patient_id', 'age'
        }

    def get_data(self) -> List[VitalSigns]:
        vital_signs = []
        try:
            response = requests.get(self.api_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if not isinstance(data, list):
                raise ValueError("API response must be a list of records")
            
            for record in data:
                try:
                    # Validate required fields
                    missing_fields = self._required_fields - set(record.keys())
                    if missing_fields:
                        logging.warning(f"Missing required fields in record: {missing_fields}")
                        continue
                        
                    vital_signs.append(VitalSigns(
                        heart_rate=float(record['heart_rate']),
                        temperature=float(record['temperature']),
                        spo2=float(record['spo2']),
                        respiratory_rate=float(record['respiratory_rate']),
                        systolic_bp=float(record['systolic_bp']),
                        diastolic_bp=float(record['diastolic_bp']),
                        timestamp=datetime.fromisoformat(record['timestamp']),
                        patient_id=record['patient_id'],
                        age=int(record['age'])
                    ))
                except (KeyError, ValueError) as e:
                    logging.error(f"Error processing record: {e}")
                    continue
                    
        except requests.RequestException as e:
            logging.error(f"API request failed: {e}")
        except ValueError as e:
            logging.error(f"Invalid API response: {e}")
            
        return vital_signs

class SimulatedStreamDataSource(DataSource):
    """Data source for simulated real-time vital signs stream."""
    def __init__(self, interval: float = 1.0, patient_id: str = "simulated", age: int = 30):
        if interval <= 0:
            raise ValueError("Interval must be positive")
        self.interval = interval
        self.patient_id = patient_id
        self.age = age
        self._last_generation = datetime.now()

    def get_data(self) -> List[VitalSigns]:
        vital_signs = []
        try:
            current_time = datetime.now()
            if (current_time - self._last_generation).total_seconds() < self.interval:
                return vital_signs
                
            # Generate one set of simulated vital signs
            vital_signs.append(VitalSigns(
                heart_rate=random.uniform(60, 100),
                temperature=random.uniform(36.5, 37.5),
                spo2=random.uniform(95, 100),
                respiratory_rate=random.uniform(12, 20),
                systolic_bp=random.uniform(110, 140),
                diastolic_bp=random.uniform(60, 90),
                timestamp=current_time,
                patient_id=self.patient_id,
                age=self.age
            ))
            self._last_generation = current_time
            
        except Exception as e:
            logging.error(f"Error generating simulated data: {e}")
            
        return vital_signs

class VitalDataIngestor:
    """Main class for ingesting and processing vital signs data."""
    
    def __init__(self, max_history_hours: int = 24):
        """Initialize the vital data ingestor."""
        self.data_sources: List[DataSource] = []
        self.vital_signs_history: Dict[str, List[VitalSigns]] = {}
        self.anomaly_detector = AnomalyDetector()
        self.baseline_comparator = BaselineComparator()
        self.max_history_hours = max_history_hours
        self._last_cleanup_time = datetime.now()
        self._cleanup_interval = timedelta(minutes=30)
        
    def add_data_source(self, source: DataSource) -> None:
        """Add a data source to the ingestor."""
        if not isinstance(source, DataSource):
            raise TypeError(f"Source must be an instance of DataSource, got {type(source)}")
        self.data_sources.append(source)
        logging.info(f"Added data source: {type(source).__name__}")
        
    def _cleanup_old_data(self) -> None:
        """Remove data older than max_history_hours."""
        current_time = datetime.now()
        if current_time - self._last_cleanup_time < self._cleanup_interval:
            return
            
        cutoff_time = current_time - timedelta(hours=self.max_history_hours)
        for patient_id in self.vital_signs_history:
            self.vital_signs_history[patient_id] = [
                vs for vs in self.vital_signs_history[patient_id]
                if vs.timestamp >= cutoff_time
            ]
        self._last_cleanup_time = current_time
        
    def ingest_data(self) -> Optional[VitalSigns]:
        """Ingest data from all sources and process it."""
        if not self.data_sources:
            logging.warning("No data sources configured")
            return None
            
        for source in self.data_sources:
            try:
                vital_signs_list = source.get_data()
                if not vital_signs_list:
                    continue
                    
                # Process the first set of vital signs
                vital_signs = vital_signs_list[0]
                
                # Update history
                if vital_signs.patient_id not in self.vital_signs_history:
                    self.vital_signs_history[vital_signs.patient_id] = []
                self.vital_signs_history[vital_signs.patient_id].append(vital_signs)
                
                # Clean up old data periodically
                self._cleanup_old_data()
                
                return vital_signs
                    
            except Exception as e:
                logging.error(f"Error ingesting data from source {type(source).__name__}: {e}")
                continue
                
        return None
        
    def analyze_vital_signs(self, vital_signs: VitalSigns) -> Dict[str, Any]:
        """Analyze vital signs for anomalies and alerts."""
        try:
            # Convert to dictionary for analysis
            vital_signs_dict = {
                'heart_rate': vital_signs.heart_rate,
                'temperature': vital_signs.temperature,
                'spo2': vital_signs.spo2,
                'respiratory_rate': vital_signs.respiratory_rate,
                'systolic_bp': vital_signs.systolic_bp,
                'diastolic_bp': vital_signs.diastolic_bp
            }
            
            # Get baseline alerts
            alerts = self.baseline_comparator.compare_vital_signs(
                vital_signs_dict,
                date_of_birth=datetime(1990, 1, 1),  # Default DOB
                gender="M"  # Default gender
            )
            
            # Get anomaly prediction
            try:
                prediction = self.anomaly_detector.predict(
                    vital_signs_dict,
                    vital_signs.timestamp
                )
            except Exception as e:
                logging.error(f"Error in anomaly detection: {e}")
                prediction = None
            
            return {
                'alerts': alerts,
                'anomaly_prediction': prediction
            }
            
        except Exception as e:
            logging.error(f"Error analyzing vital signs: {e}")
            return {'alerts': [], 'anomaly_prediction': None}
            
    def get_patient_history(self, patient_id: str, hours: int = 24) -> List[VitalSigns]:
        """Get patient history for the specified time period."""
        if patient_id not in self.vital_signs_history:
            return []
            
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            vs for vs in self.vital_signs_history[patient_id]
            if vs.timestamp >= cutoff_time
        ]
        
    def save_patient_history(self, patient_id: str, file_path: str) -> None:
        """Save patient history to a JSON file."""
        if patient_id not in self.vital_signs_history:
            raise ValueError(f"No history found for patient {patient_id}")
            
        try:
            history_data = [
                vs.to_dict() for vs in self.vital_signs_history[patient_id]
            ]
            with open(file_path, 'w') as f:
                json.dump(history_data, f, indent=2)
        except Exception as e:
            raise IOError(f"Error saving patient history: {e}")
            
    def load_patient_history(self, file_path: str) -> None:
        """Load patient history from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                history_data = json.load(f)
                
            for record in history_data:
                vs = VitalSigns(
                    heart_rate=record['heart_rate'],
                    temperature=record['temperature'],
                    spo2=record['spo2'],
                    respiratory_rate=record['respiratory_rate'],
                    systolic_bp=record['systolic_bp'],
                    diastolic_bp=record['diastolic_bp'],
                    timestamp=datetime.fromisoformat(record['timestamp']),
                    patient_id=record['patient_id'],
                    age=record['age']
                )
                
                if vs.patient_id not in self.vital_signs_history:
                    self.vital_signs_history[vs.patient_id] = []
                self.vital_signs_history[vs.patient_id].append(vs)
                
        except Exception as e:
            raise IOError(f"Error loading patient history: {e}") 
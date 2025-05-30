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

from src.data.models import VitalSigns
from src.data.data_sources import DataSource
from src.analysis.anomaly_detector import AnomalyDetector, AnomalyPrediction
from src.analysis.baseline_comparator import BaselineComparator, Alert

@dataclass
class VitalSigns:
    """Data class to hold vital signs data with validation."""
    heart_rate: float
    temperature: float
    spo2: float
    respiratory_rate: float
    systolic_bp: float
    diastolic_bp: float
    timestamp: datetime

    def __post_init__(self):
        """Validate vital signs data after initialization."""
        if not (40 <= self.heart_rate <= 200):
            raise ValueError(f"Heart rate {self.heart_rate} is outside normal range (40-200)")
        if not (35 <= self.temperature <= 42):
            raise ValueError(f"Temperature {self.temperature} is outside normal range (35-42)")
        if not (70 <= self.spo2 <= 100):
            raise ValueError(f"SpO2 {self.spo2} is outside normal range (70-100)")
        if not (8 <= self.respiratory_rate <= 40):
            raise ValueError(f"Respiratory rate {self.respiratory_rate} is outside normal range (8-40)")
        if not (70 <= self.systolic_bp <= 200):
            raise ValueError(f"Systolic BP {self.systolic_bp} is outside normal range (70-200)")
        if not (40 <= self.diastolic_bp <= 120):
            raise ValueError(f"Diastolic BP {self.diastolic_bp} is outside normal range (40-120)")
    
    def to_dict(self) -> Dict[str, float]:
        """Convert vital signs to dictionary format."""
        return {
            'heart_rate': self.heart_rate,
            'temperature': self.temperature,
            'spo2': self.spo2,
            'respiratory_rate': self.respiratory_rate,
            'systolic_bp': self.systolic_bp,
            'diastolic_bp': self.diastolic_bp
        }

class DataSource(ABC):
    """Abstract base class for data sources."""
    @abstractmethod
    def get_data(self) -> List[VitalSigns]:
        """Retrieve and parse data from the source."""
        pass

class CSVDataSource(DataSource):
    """Data source for CSV files."""
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_data(self) -> List[VitalSigns]:
        vital_signs = []
        with open(self.file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    vital_signs.append(VitalSigns(
                        heart_rate=float(row['heart_rate']),
                        temperature=float(row['temperature']),
                        spo2=float(row['spo2']),
                        respiratory_rate=float(row['respiratory_rate']),
                        systolic_bp=float(row['systolic_bp']),
                        diastolic_bp=float(row['diastolic_bp']),
                        timestamp=datetime.fromisoformat(row['timestamp'])
                    ))
                except (KeyError, ValueError) as e:
                    print(f"Error processing row: {e}")
        return vital_signs

class APIDataSource(DataSource):
    """Data source for JSON API endpoints."""
    def __init__(self, api_url: str):
        self.api_url = api_url

    def get_data(self) -> List[VitalSigns]:
        try:
            response = requests.get(self.api_url)
            response.raise_for_status()
            data = response.json()
            
            vital_signs = []
            for record in data:
                try:
                    vital_signs.append(VitalSigns(
                        heart_rate=float(record['heart_rate']),
                        temperature=float(record['temperature']),
                        spo2=float(record['spo2']),
                        respiratory_rate=float(record['respiratory_rate']),
                        systolic_bp=float(record['systolic_bp']),
                        diastolic_bp=float(record['diastolic_bp']),
                        timestamp=datetime.fromisoformat(record['timestamp'])
                    ))
                except (KeyError, ValueError) as e:
                    print(f"Error processing record: {e}")
            return vital_signs
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            return []

class SimulatedStreamDataSource(DataSource):
    """Data source for simulated real-time vital signs stream."""
    def __init__(self, interval: float = 1.0):
        self.interval = interval

    def get_data(self) -> List[VitalSigns]:
        vital_signs = []
        try:
            # Generate one set of simulated vital signs
            vital_signs.append(VitalSigns(
                heart_rate=random.uniform(60, 100),
                temperature=random.uniform(36.5, 37.5),
                spo2=random.uniform(95, 100),
                respiratory_rate=random.uniform(12, 20),
                systolic_bp=random.uniform(110, 140),
                diastolic_bp=random.uniform(60, 90),
                timestamp=datetime.now()
            ))
            time.sleep(self.interval)
        except Exception as e:
            print(f"Error generating simulated data: {e}")
        return vital_signs

class VitalDataIngestor:
    """Main class for ingesting and processing vital signs data."""
    
    def __init__(self):
        """Initialize the vital data ingestor."""
        self.data_sources: List[DataSource] = []
        self.vital_signs_history: Dict[str, List[VitalSigns]] = {}
        self.anomaly_detector = AnomalyDetector()
        self.baseline_comparator = BaselineComparator()
        
    def add_data_source(self, source: DataSource) -> None:
        """Add a data source to the ingestor."""
        self.data_sources.append(source)
        
    def ingest_data(self) -> List[VitalSigns]:
        """Ingest data from all sources and process it."""
        all_vital_signs = []
        
        for source in self.data_sources:
            try:
                vital_signs = source.get_data()
                all_vital_signs.extend(vital_signs)
                
                # Update history for each patient
                for vs in vital_signs:
                    if vs.patient_id not in self.vital_signs_history:
                        self.vital_signs_history[vs.patient_id] = []
                    self.vital_signs_history[vs.patient_id].append(vs)
                    
                    # Keep only last 24 hours of data
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    self.vital_signs_history[vs.patient_id] = [
                        vs for vs in self.vital_signs_history[vs.patient_id]
                        if vs.timestamp >= cutoff_time
                    ]
                    
            except Exception as e:
                print(f"Error ingesting data from source: {e}")
                continue
                
        return all_vital_signs
        
    def analyze_vital_signs(self, vital_signs: VitalSigns) -> Dict[str, Any]:
        """Analyze vital signs and return results."""
        # Get patient history
        patient_history = self.vital_signs_history.get(vital_signs.patient_id, [])
        
        # Detect anomalies
        anomaly_prediction = self.anomaly_detector.predict(
            vital_signs,
            patient_history
        )
        
        # Compare with baseline
        alerts = self.baseline_comparator.compare_vital_signs(
            vital_signs,
            vital_signs.age
        )
        
        return {
            'vital_signs': vital_signs.to_dict(),
            'anomaly_prediction': anomaly_prediction.to_dict() if anomaly_prediction else None,
            'alerts': [alert.to_dict() for alert in alerts]
        }
        
    def get_patient_history(self, patient_id: str, hours: int = 24) -> List[VitalSigns]:
        """Get patient's vital signs history for the specified time period."""
        if patient_id not in self.vital_signs_history:
            return []
            
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            vs for vs in self.vital_signs_history[patient_id]
            if vs.timestamp >= cutoff_time
        ]
        
    def save_patient_history(self, patient_id: str, file_path: str) -> None:
        """Save patient's vital signs history to a JSON file."""
        if patient_id not in self.vital_signs_history:
            return
            
        data = [vs.to_dict() for vs in self.vital_signs_history[patient_id]]
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def load_patient_history(self, file_path: str) -> None:
        """Load patient's vital signs history from a JSON file."""
        if not os.path.exists(file_path):
            return
            
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        for item in data:
            vital_signs = VitalSigns.from_dict(item)
            if vital_signs.patient_id not in self.vital_signs_history:
                self.vital_signs_history[vital_signs.patient_id] = []
            self.vital_signs_history[vital_signs.patient_id].append(vital_signs) 
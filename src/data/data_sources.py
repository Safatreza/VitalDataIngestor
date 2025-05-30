from abc import ABC, abstractmethod
import csv
import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import requests

from .models import VitalSigns

class DataSource(ABC):
    """Abstract base class for data sources."""
    
    @abstractmethod
    def get_vital_signs(self) -> List[VitalSigns]:
        """Get vital signs from the data source."""
        pass

class CSVDataSource(DataSource):
    """Data source for reading vital signs from CSV files."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        
    def get_vital_signs(self) -> List[VitalSigns]:
        vital_signs = []
        with open(self.file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    vital_signs.append(VitalSigns(
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        heart_rate=float(row['heart_rate']),
                        temperature=float(row['temperature']),
                        spo2=float(row['spo2']),
                        respiratory_rate=float(row['respiratory_rate']),
                        systolic_bp=float(row['systolic_bp']),
                        diastolic_bp=float(row['diastolic_bp']),
                        patient_id=row['patient_id'],
                        age=int(row['age']) if 'age' in row else None,
                        gender=row['gender'] if 'gender' in row else None
                    ))
                except (ValueError, KeyError) as e:
                    print(f"Error parsing row: {e}")
                    continue
        return vital_signs

class APIDataSource(DataSource):
    """Data source for reading vital signs from a REST API."""
    
    def __init__(self, api_url: str, api_key: Optional[str] = None):
        self.api_url = api_url
        self.api_key = api_key
        
    def get_vital_signs(self) -> List[VitalSigns]:
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
            
        try:
            response = requests.get(self.api_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            vital_signs = []
            for item in data:
                try:
                    vital_signs.append(VitalSigns.from_dict(item))
                except (ValueError, KeyError) as e:
                    print(f"Error parsing API response: {e}")
                    continue
            return vital_signs
        except requests.RequestException as e:
            print(f"Error fetching data from API: {e}")
            return []

class SimulatedStreamDataSource(DataSource):
    """Data source that simulates a stream of vital signs data."""
    
    def __init__(self, interval: float = 1.0, abnormal_probability: float = 0.2):
        self.interval = interval
        self.abnormal_probability = abnormal_probability
        self.last_reading = None
        
    def _generate_vital_signs(self, pattern: str = 'normal') -> VitalSigns:
        """Generate a single set of vital signs."""
        if pattern == 'normal':
            vital_signs = {
                'heart_rate': random.uniform(60, 100),
                'temperature': random.uniform(36.5, 37.5),
                'spo2': random.uniform(95, 100),
                'respiratory_rate': random.uniform(12, 20),
                'systolic_bp': random.uniform(110, 140),
                'diastolic_bp': random.uniform(60, 90)
            }
        else:  # abnormal
            vital_signs = {
                'heart_rate': random.uniform(40, 200),
                'temperature': random.uniform(35, 42),
                'spo2': random.uniform(70, 100),
                'respiratory_rate': random.uniform(8, 40),
                'systolic_bp': random.uniform(70, 200),
                'diastolic_bp': random.uniform(40, 120)
            }
            
        return VitalSigns(
            timestamp=datetime.now(),
            patient_id=f"PATIENT_{random.randint(1, 100)}",
            age=random.randint(18, 90),
            gender=random.choice(['M', 'F']),
            **vital_signs
        )
        
    def get_vital_signs(self) -> List[VitalSigns]:
        """Get a single reading from the simulated stream."""
        time.sleep(self.interval)
        pattern = 'abnormal' if random.random() < self.abnormal_probability else 'normal'
        self.last_reading = self._generate_vital_signs(pattern)
        return [self.last_reading] 
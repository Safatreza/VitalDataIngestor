import csv
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from ..data.models import VitalSigns

class MockDataGenerator:
    """Class for generating mock vital signs data."""
    
    def __init__(self):
        """Initialize the mock data generator with normal and abnormal ranges."""
        self.normal_ranges = {
            'heart_rate': (60, 100),
            'temperature': (36.5, 37.5),
            'spo2': (95, 100),
            'respiratory_rate': (12, 20),
            'systolic_bp': (110, 140),
            'diastolic_bp': (60, 90)
        }
        
        self.abnormal_ranges = {
            'heart_rate': (40, 200),
            'temperature': (35, 42),
            'spo2': (70, 100),
            'respiratory_rate': (8, 40),
            'systolic_bp': (70, 200),
            'diastolic_bp': (40, 120)
        }
        
    def _generate_vital_signs(self, pattern: str = 'normal') -> VitalSigns:
        """Generate a single set of vital signs."""
        ranges = self.normal_ranges if pattern == 'normal' else self.abnormal_ranges
        
        vital_signs = {
            'heart_rate': random.uniform(*ranges['heart_rate']),
            'temperature': random.uniform(*ranges['temperature']),
            'spo2': random.uniform(*ranges['spo2']),
            'respiratory_rate': random.uniform(*ranges['respiratory_rate']),
            'systolic_bp': random.uniform(*ranges['systolic_bp']),
            'diastolic_bp': random.uniform(*ranges['diastolic_bp'])
        }
        
        return VitalSigns(
            timestamp=datetime.now(),
            patient_id=f"PATIENT_{random.randint(1, 100)}",
            age=random.randint(18, 90),
            gender=random.choice(['M', 'F']),
            validate_ranges=False,  # Don't validate ranges for generated data
            **vital_signs
        )
        
    def generate_dataset(self, num_patients: int, duration_hours: int, 
                        output_file: str, abnormal_probability: float = 0.2) -> None:
        """Generate a dataset of mock vital signs and save to CSV."""
        # Generate data for each patient
        all_vital_signs = []
        start_time = datetime.now() - timedelta(hours=duration_hours)
        
        for patient_id in range(1, num_patients + 1):
            current_time = start_time
            while current_time <= datetime.now():
                # Generate vital signs
                pattern = 'abnormal' if random.random() < abnormal_probability else 'normal'
                vital_signs = self._generate_vital_signs(pattern)
                vital_signs.patient_id = f"PATIENT_{patient_id}"
                vital_signs.timestamp = current_time
                all_vital_signs.append(vital_signs)
                
                # Move to next reading (every 5 minutes)
                current_time += timedelta(minutes=5)
                
        # Save to CSV
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'patient_id', 'age', 'gender',
                'heart_rate', 'temperature', 'spo2',
                'respiratory_rate', 'systolic_bp', 'diastolic_bp'
            ])
            writer.writeheader()
            for vs in all_vital_signs:
                writer.writerow(vs.to_dict())
                
    def generate_single_reading(self) -> VitalSigns:
        """Generate a single set of vital signs."""
        pattern = 'abnormal' if random.random() < 0.2 else 'normal'
        return self._generate_vital_signs(pattern) 
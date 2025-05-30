from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class VitalSigns:
    """Data class for storing vital signs measurements."""
    timestamp: datetime
    heart_rate: float
    temperature: float
    spo2: float
    respiratory_rate: float
    systolic_bp: float
    diastolic_bp: float
    patient_id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    validate_ranges: bool = True

    def __post_init__(self):
        """Validate vital signs ranges after initialization."""
        if not self.validate_ranges:
            return
            
        if not (60 <= self.heart_rate <= 200):
            raise ValueError(f"Heart rate {self.heart_rate} outside normal range (60-200)")
        if not (35 <= self.temperature <= 42):
            raise ValueError(f"Temperature {self.temperature} outside normal range (35-42)")
        if not (70 <= self.spo2 <= 100):
            raise ValueError(f"SpO2 {self.spo2} outside normal range (70-100)")
        if not (8 <= self.respiratory_rate <= 40):
            raise ValueError(f"Respiratory rate {self.respiratory_rate} outside normal range (8-40)")
        if not (70 <= self.systolic_bp <= 200):
            raise ValueError(f"Systolic BP {self.systolic_bp} outside normal range (70-200)")
        if not (40 <= self.diastolic_bp <= 120):
            raise ValueError(f"Diastolic BP {self.diastolic_bp} outside normal range (40-120)")

    def to_dict(self) -> Dict[str, Any]:
        """Convert vital signs to dictionary format."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'heart_rate': self.heart_rate,
            'temperature': self.temperature,
            'spo2': self.spo2,
            'respiratory_rate': self.respiratory_rate,
            'systolic_bp': self.systolic_bp,
            'diastolic_bp': self.diastolic_bp,
            'patient_id': self.patient_id,
            'age': self.age,
            'gender': self.gender
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VitalSigns':
        """Create VitalSigns instance from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data) 
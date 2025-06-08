import json
import csv
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

class AlertSeverity(Enum):
    """Enumeration for alert severity levels."""
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

@dataclass
class Alert:
    """Data class for vital signs alerts."""
    vital_sign: str
    message: str
    severity: AlertSeverity
    value: float
    baseline_min: float
    baseline_max: float

@dataclass
class BaselineRange:
    """Data class for vital signs baseline ranges."""
    min_value: float
    max_value: float
    severity_threshold: float  # Percentage deviation from range to trigger critical alert

class BaselineComparator:
    """Class for comparing vital signs against baseline ranges."""
    
    def __init__(self):
        """Initialize the baseline comparator."""
        self.baseline_ranges = {}
    
    def load_baselines_from_json(self, file_path: str) -> None:
        """Load baseline ranges from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                self.baseline_ranges = json.load(f)
        except FileNotFoundError:
            logging.warning(f"Warning: {file_path} not found.")
            self.baseline_ranges = {}
    
    def _calculate_age_group(self, date_of_birth: datetime) -> str:
        """Calculate age group based on date of birth."""
        age = (datetime.now() - date_of_birth).days / 365.25
        
        if age < 1:
            return "infant"
        elif age < 12:
            return "child"
        elif age < 18:
            return "adolescent"
        elif age < 65:
            return "adult"
        else:
            return "elderly"
    
    def _get_baseline_range(self, vital_sign: str, age_group: str, gender: str) -> Optional[Dict[str, float]]:
        """Get baseline range for a vital sign based on age group and gender."""
        try:
            return self.baseline_ranges[vital_sign][age_group][gender]
        except KeyError:
            return None
    
    def compare_vital_signs(
        self,
        vital_signs: Dict[str, float],
        date_of_birth: datetime,
        gender: str
    ) -> List[Alert]:
        """Compare vital signs against baseline ranges and generate alerts."""
        alerts = []
        age_group = self._calculate_age_group(date_of_birth)
        
        for vital_sign, value in vital_signs.items():
            baseline = self._get_baseline_range(vital_sign, age_group, gender)
            if baseline is None:
                continue
            
            min_value = baseline['min']
            max_value = baseline['max']
            warning_min = baseline.get('warning_min', min_value)
            warning_max = baseline.get('warning_max', max_value)
            
            # Check for critical values
            if value < min_value or value > max_value:
                severity = AlertSeverity.CRITICAL
                message = f"{vital_sign} is critically {'low' if value < min_value else 'high'}"
            # Check for warning values
            elif value < warning_min or value > warning_max:
                severity = AlertSeverity.WARNING
                message = f"{vital_sign} is {'low' if value < warning_min else 'high'}"
            else:
                severity = AlertSeverity.NORMAL
                message = f"{vital_sign} is within normal range"
            
            alerts.append(Alert(
                vital_sign=vital_sign,
                message=message,
                severity=severity,
                value=value,
                baseline_min=min_value,
                baseline_max=max_value
            ))
        
        return alerts
    
    def get_baseline_range(
        self,
        vital_sign: str,
        age_group: str,
        gender: str
    ) -> Optional[BaselineRange]:
        """Get the baseline range for a specific vital sign, age group, and gender."""
        try:
            return self.baseline_ranges[vital_sign][age_group][gender]
        except KeyError:
            return None 
"""
Dummy Sensor Module for Raspberry Pi

This module simulates various vital sign sensors that might be connected to a Raspberry Pi.
It generates realistic sensor readings with configurable parameters and noise.
"""

import random
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List
import numpy as np
from datetime import datetime

@dataclass
class SensorReading:
    """Represents a single reading from a vital sign sensor."""
    value: float
    timestamp: datetime
    sensor_id: str
    unit: str
    confidence: float

class DummySensor:
    """
    Simulates multiple vital sign sensors with realistic readings and noise.
    
    Attributes:
        sensor_id (str): Unique identifier for the sensor
        noise_level (float): Amount of random noise to add to readings
        sampling_rate (float): Readings per second
    """
    
    # Define normal ranges for different vital signs
    VITAL_SIGNS = {
        'heart_rate': {
            'unit': 'bpm',
            'normal_range': (60, 100),
            'sensor_id': 'hr_sensor'
        },
        'temperature': {
            'unit': '°C',
            'normal_range': (36.5, 37.5),
            'sensor_id': 'temp_sensor'
        },
        'spo2': {
            'unit': '%',
            'normal_range': (95, 100),
            'sensor_id': 'spo2_sensor'
        },
        'respiratory_rate': {
            'unit': 'bpm',
            'normal_range': (12, 20),
            'sensor_id': 'resp_sensor'
        },
        'systolic_bp': {
            'unit': 'mmHg',
            'normal_range': (110, 140),
            'sensor_id': 'bp_sensor'
        },
        'diastolic_bp': {
            'unit': 'mmHg',
            'normal_range': (60, 90),
            'sensor_id': 'bp_sensor'
        }
    }
    
    def __init__(
        self,
        noise_level: float = 0.1,
        sampling_rate: float = 1.0
    ):
        """
        Initialize the dummy sensor system.
        
        Args:
            noise_level: Amount of random noise (0-1)
            sampling_rate: Readings per second
        """
        self.noise_level = noise_level
        self.sampling_rate = sampling_rate
        self._last_readings: Dict[str, float] = {}
        self._range_sizes: Dict[str, float] = {
            vital_sign: config['normal_range'][1] - config['normal_range'][0]
            for vital_sign, config in self.VITAL_SIGNS.items()
        }
        
    def _add_noise(self, value: float, vital_sign: str) -> float:
        """
        Add realistic noise to a sensor reading.
        
        Args:
            value: Base reading value
            vital_sign: Type of vital sign
            
        Returns:
            float: Reading with added noise
        """
        noise = np.random.normal(0, self.noise_level * self._range_sizes[vital_sign])
        return value + noise
    
    def _generate_realistic_value(self, vital_sign: str) -> float:
        """
        Generate a realistic value for the vital sign.
        
        Args:
            vital_sign: Type of vital sign
            
        Returns:
            float: Generated value within normal range
        """
        normal_range = self.VITAL_SIGNS[vital_sign]['normal_range']
        
        if vital_sign not in self._last_readings:
            value = random.uniform(*normal_range)
        else:
            max_change = self._range_sizes[vital_sign] * 0.1
            value = self._last_readings[vital_sign] + random.uniform(-max_change, max_change)
            value = max(min(value, normal_range[1]), normal_range[0])
        
        self._last_readings[vital_sign] = value
        return value
    
    def _calculate_confidence(self, value: float, vital_sign: str) -> float:
        """
        Calculate confidence score for a reading.
        
        Args:
            value: Reading value
            vital_sign: Type of vital sign
            
        Returns:
            float: Confidence score between 0 and 1
        """
        normal_range = self.VITAL_SIGNS[vital_sign]['normal_range']
        distance_from_normal = min(
            abs(value - normal_range[0]),
            abs(value - normal_range[1])
        )
        return max(0, 1 - (distance_from_normal / self._range_sizes[vital_sign]))
    
    def read_vital_sign(self, vital_sign: str) -> SensorReading:
        """
        Generate a reading for a specific vital sign.
        
        Args:
            vital_sign: Type of vital sign to read
            
        Returns:
            SensorReading: New reading with timestamp and confidence
        """
        if vital_sign not in self.VITAL_SIGNS:
            raise ValueError(f"Unknown vital sign: {vital_sign}")
            
        config = self.VITAL_SIGNS[vital_sign]
        base_value = self._generate_realistic_value(vital_sign)
        noisy_value = self._add_noise(base_value, vital_sign)
        confidence = self._calculate_confidence(noisy_value, vital_sign)
        
        return SensorReading(
            value=noisy_value,
            timestamp=datetime.now(),
            sensor_id=config['sensor_id'],
            unit=config['unit'],
            confidence=confidence
        )
    
    def read_all_vital_signs(self) -> Dict[str, SensorReading]:
        """
        Generate readings for all vital signs.
        
        Returns:
            Dict[str, SensorReading]: Dictionary of readings for each vital sign
        """
        return {
            vital_sign: self.read_vital_sign(vital_sign)
            for vital_sign in self.VITAL_SIGNS
        }
    
    def read_continuous(self, duration: float = 60.0) -> Dict[str, Dict[str, List[float]]]:
        """
        Generate continuous readings for all vital signs.
        
        Args:
            duration: Duration in seconds to generate readings
            
        Returns:
            Dict[str, Dict[str, List[float]]]: Dictionary of readings for each vital sign
        """
        num_readings = int(duration * self.sampling_rate)
        readings = {
            vital_sign: {
                'timestamps': [],
                'values': [],
                'confidence': []
            }
            for vital_sign in self.VITAL_SIGNS
        }
        
        for _ in range(num_readings):
            vital_signs = self.read_all_vital_signs()
            for vital_sign, reading in vital_signs.items():
                readings[vital_sign]['timestamps'].append(reading.timestamp)
                readings[vital_sign]['values'].append(reading.value)
                readings[vital_sign]['confidence'].append(reading.confidence)
            time.sleep(1.0 / self.sampling_rate)
            
        return readings 
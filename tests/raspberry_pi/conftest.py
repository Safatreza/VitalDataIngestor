"""
Shared test fixtures for Raspberry Pi module tests.
"""

import pytest
from src.raspberry_pi.dummy_sensor import DummySensor, SensorReading

@pytest.fixture
def vital_signs_config():
    """Configuration for different vital signs."""
    return {
        'heart_rate': {
            'normal_range': (60, 100),
            'unit': 'bpm',
            'noise_level': 0.1
        },
        'spo2': {
            'normal_range': (95, 100),
            'unit': '%',
            'noise_level': 0.05
        },
        'temperature': {
            'normal_range': (36.1, 37.2),
            'unit': '°C',
            'noise_level': 0.02
        },
        'respiratory_rate': {
            'normal_range': (12, 20),
            'unit': 'bpm',
            'noise_level': 0.15
        }
    }

@pytest.fixture
def sensor_factory(vital_signs_config):
    """Factory function to create sensors for different vital signs."""
    def create_sensor(vital_sign: str, sensor_id: str) -> DummySensor:
        config = vital_signs_config[vital_sign]
        return DummySensor(
            sensor_id=sensor_id,
            vital_sign=vital_sign,
            unit=config['unit'],
            normal_range=config['normal_range'],
            noise_level=config['noise_level']
        )
    return create_sensor

@pytest.fixture
def sample_readings():
    """Generate a set of sample readings for testing."""
    return {
        'timestamps': [1.0, 2.0, 3.0],
        'values': [75.0, 76.0, 77.0],
        'confidence': [0.9, 0.95, 0.98]
    } 
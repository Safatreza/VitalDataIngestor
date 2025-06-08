"""
Unit tests for the DummySensor class.
"""

import pytest
import time
from src.raspberry_pi.dummy_sensor import DummySensor, SensorReading

@pytest.fixture
def heart_rate_sensor():
    """Create a heart rate sensor fixture."""
    return DummySensor(
        sensor_id="hr_001",
        vital_sign="heart_rate",
        unit="bpm",
        normal_range=(60, 100),
        noise_level=0.1,
        sampling_rate=1.0
    )

@pytest.fixture
def spo2_sensor():
    """Create an SpO2 sensor fixture."""
    return DummySensor(
        sensor_id="spo2_001",
        vital_sign="spo2",
        unit="%",
        normal_range=(95, 100),
        noise_level=0.05,
        sampling_rate=1.0
    )

def test_sensor_initialization(heart_rate_sensor):
    """Test sensor initialization with correct parameters."""
    assert heart_rate_sensor.sensor_id == "hr_001"
    assert heart_rate_sensor.vital_sign == "heart_rate"
    assert heart_rate_sensor.unit == "bpm"
    assert heart_rate_sensor.normal_range == (60, 100)
    assert heart_rate_sensor.noise_level == 0.1
    assert heart_rate_sensor.sampling_rate == 1.0
    assert heart_rate_sensor._last_reading is None

def test_single_reading(heart_rate_sensor):
    """Test single reading generation."""
    reading = heart_rate_sensor.read()
    
    # Check reading type and attributes
    assert isinstance(reading, SensorReading)
    assert reading.sensor_id == "hr_001"
    assert reading.unit == "bpm"
    assert isinstance(reading.value, float)
    assert isinstance(reading.timestamp, float)
    assert isinstance(reading.confidence, float)
    
    # Check value is within normal range
    assert 60 <= reading.value <= 100
    
    # Check confidence is between 0 and 1
    assert 0 <= reading.confidence <= 1

def test_continuous_readings(heart_rate_sensor):
    """Test continuous reading generation."""
    duration = 2.0  # 2 seconds
    readings = heart_rate_sensor.read_continuous(duration)
    
    # Check readings structure
    assert isinstance(readings, dict)
    assert set(readings.keys()) == {'timestamps', 'values', 'confidence'}
    assert len(readings['timestamps']) == len(readings['values']) == len(readings['confidence'])
    
    # Check all values are within normal range
    assert all(60 <= v <= 100 for v in readings['values'])
    
    # Check timestamps are sequential
    timestamps = readings['timestamps']
    assert all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))
    
    # Check confidence values
    assert all(0 <= c <= 1 for c in readings['confidence'])

def test_noise_level_impact(heart_rate_sensor, spo2_sensor):
    """Test that different noise levels affect readings differently."""
    # Get multiple readings from each sensor
    hr_readings = [heart_rate_sensor.read().value for _ in range(10)]
    spo2_readings = [spo2_sensor.read().value for _ in range(10)]
    
    # Calculate standard deviations
    hr_std = sum((x - sum(hr_readings)/len(hr_readings))**2 for x in hr_readings) / len(hr_readings)
    spo2_std = sum((x - sum(spo2_readings)/len(spo2_readings))**2 for x in spo2_readings) / len(spo2_readings)
    
    # Higher noise level should result in higher standard deviation
    assert hr_std > spo2_std

def test_sampling_rate(heart_rate_sensor):
    """Test that sampling rate affects reading frequency."""
    start_time = time.time()
    readings = heart_rate_sensor.read_continuous(duration=1.0)
    end_time = time.time()
    
    # For 1 second duration and 1 Hz sampling rate, we should get approximately 1 reading
    assert abs(len(readings['timestamps']) - 1) <= 1
    
    # Check that the total time is approximately 1 second
    assert abs(end_time - start_time - 1.0) <= 0.1

def test_value_smoothness(heart_rate_sensor):
    """Test that consecutive readings show smooth transitions."""
    readings = heart_rate_sensor.read_continuous(duration=5.0)
    values = readings['values']
    
    # Calculate maximum change between consecutive readings
    max_change = max(abs(values[i+1] - values[i]) for i in range(len(values)-1))
    
    # Maximum change should be less than 10% of the range
    range_size = heart_rate_sensor.normal_range[1] - heart_rate_sensor.normal_range[0]
    assert max_change <= range_size * 0.1 
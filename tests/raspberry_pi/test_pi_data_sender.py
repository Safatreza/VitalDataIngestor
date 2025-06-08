"""
Unit tests for the PiDataSender class.
"""

import pytest
import json
from unittest.mock import Mock, patch
from src.raspberry_pi.pi_data_sender import PiDataSender
from src.raspberry_pi.dummy_sensor import SensorReading

@pytest.fixture
def mock_mqtt_client():
    """Create a mock MQTT client."""
    with patch('paho.mqtt.client.Client') as mock:
        client = Mock()
        mock.return_value = client
        yield client

@pytest.fixture
def mock_requests():
    """Create a mock requests module."""
    with patch('requests.post') as mock:
        yield mock

@pytest.fixture
def sample_reading():
    """Create a sample sensor reading."""
    return SensorReading(
        value=75.5,
        timestamp=1234567890.0,
        sensor_id="hr_001",
        unit="bpm",
        confidence=0.95
    )

@pytest.fixture
def http_sender():
    """Create an HTTP sender instance."""
    return PiDataSender(
        server_url="http://test.server",
        protocol="http"
    )

@pytest.fixture
def mqtt_sender(mock_mqtt_client):
    """Create an MQTT sender instance."""
    return PiDataSender(
        mqtt_broker="test.broker",
        mqtt_port=1883,
        protocol="mqtt"
    )

def test_http_sender_initialization(http_sender):
    """Test HTTP sender initialization."""
    assert http_sender.server_url == "http://test.server"
    assert http_sender.protocol == "http"
    assert not hasattr(http_sender, 'mqtt_client')

def test_mqtt_sender_initialization(mqtt_sender, mock_mqtt_client):
    """Test MQTT sender initialization."""
    assert mqtt_sender.mqtt_broker == "test.broker"
    assert mqtt_sender.mqtt_port == 1883
    assert mqtt_sender.protocol == "mqtt"
    mock_mqtt_client.connect.assert_called_once_with("test.broker", 1883)
    mock_mqtt_client.loop_start.assert_called_once()

def test_invalid_protocol():
    """Test initialization with invalid protocol."""
    with pytest.raises(ValueError, match="Protocol must be either 'mqtt' or 'http'"):
        PiDataSender(protocol="invalid")

def test_http_send_reading(http_sender, mock_requests, sample_reading):
    """Test sending a single reading via HTTP."""
    mock_requests.return_value.status_code = 200
    
    success = http_sender.send_reading(sample_reading)
    
    assert success
    mock_requests.assert_called_once_with(
        "http://test.server/vital_signs",
        json={
            'value': 75.5,
            'timestamp': 1234567890.0,
            'sensor_id': 'hr_001',
            'unit': 'bpm',
            'confidence': 0.95
        },
        headers={'Content-Type': 'application/json'}
    )

def test_mqtt_send_reading(mqtt_sender, mock_mqtt_client, sample_reading):
    """Test sending a single reading via MQTT."""
    mock_mqtt_client.publish.return_value.rc = 0
    
    success = mqtt_sender.send_reading(sample_reading)
    
    assert success
    mock_mqtt_client.publish.assert_called_once_with(
        "vital_signs",
        json.dumps({
            'value': 75.5,
            'timestamp': 1234567890.0,
            'sensor_id': 'hr_001',
            'unit': 'bpm',
            'confidence': 0.95
        }),
        qos=1
    )

def test_http_send_batch(http_sender, mock_requests):
    """Test sending a batch of readings via HTTP."""
    mock_requests.return_value.status_code = 200
    batch_data = {
        'timestamps': [1.0, 2.0],
        'values': [75.0, 76.0],
        'confidence': [0.9, 0.95]
    }
    
    success = http_sender.send_batch(batch_data)
    
    assert success
    mock_requests.assert_called_once_with(
        "http://test.server/vital_signs",
        json={
            'batch': True,
            'readings': batch_data
        },
        headers={'Content-Type': 'application/json'}
    )

def test_mqtt_send_batch(mqtt_sender, mock_mqtt_client):
    """Test sending a batch of readings via MQTT."""
    mock_mqtt_client.publish.return_value.rc = 0
    batch_data = {
        'timestamps': [1.0, 2.0],
        'values': [75.0, 76.0],
        'confidence': [0.9, 0.95]
    }
    
    success = mqtt_sender.send_batch(batch_data)
    
    assert success
    mock_mqtt_client.publish.assert_called_once_with(
        "vital_signs",
        json.dumps({
            'batch': True,
            'readings': batch_data
        }),
        qos=1
    )

def test_http_send_failure(http_sender, mock_requests, sample_reading):
    """Test HTTP send failure handling."""
    mock_requests.side_effect = Exception("Connection error")
    
    success = http_sender.send_reading(sample_reading)
    
    assert not success

def test_mqtt_send_failure(mqtt_sender, mock_mqtt_client, sample_reading):
    """Test MQTT send failure handling."""
    mock_mqtt_client.publish.side_effect = Exception("MQTT error")
    
    success = mqtt_sender.send_reading(sample_reading)
    
    assert not success

def test_mqtt_cleanup(mqtt_sender, mock_mqtt_client):
    """Test MQTT client cleanup."""
    mqtt_sender.close()
    
    mock_mqtt_client.loop_stop.assert_called_once()
    mock_mqtt_client.disconnect.assert_called_once() 
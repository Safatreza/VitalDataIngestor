"""
Raspberry Pi Integration Module

This module provides functionality for:
- Simulating vital sign sensors on Raspberry Pi
- Sending sensor data to the main system via MQTT/HTTP
"""

from .dummy_sensor import DummySensor
from .pi_data_sender import PiDataSender

__all__ = ['DummySensor', 'PiDataSender'] 
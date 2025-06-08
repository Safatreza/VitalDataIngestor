"""
Raspberry Pi Data Sender Module

This module handles sending sensor data from Raspberry Pi to the main system
using either MQTT or HTTP protocols.
"""

import json
import time
from typing import Dict, Optional, Union, Any, List
import paho.mqtt.client as mqtt
import requests
from dataclasses import asdict
from datetime import datetime
import logging

from .dummy_sensor import SensorReading, DummySensor
from src.data.models import VitalSigns
from src.data.data_sources import DataSource

class PiDataSender(DataSource):
    """
    Handles sending sensor data to the main system via MQTT or HTTP.
    Implements the DataSource interface for integration with the main system.
    
    Attributes:
        sensor (DummySensor): Sensor instance for reading vital signs
        server_url (str): Base URL for HTTP requests
        mqtt_broker (str): MQTT broker address
        mqtt_port (int): MQTT broker port
        mqtt_topic (str): MQTT topic for publishing
        protocol (str): Communication protocol ('mqtt' or 'http')
        patient_id (str): ID of the patient being monitored
    """
    
    def __init__(
        self,
        sensor: DummySensor,
        patient_id: str = "default",
        server_url: str = "http://localhost:8000",
        mqtt_broker: str = "localhost",
        mqtt_port: int = 1883,
        mqtt_topic: str = "vital_signs",
        protocol: str = "http"
    ):
        """
        Initialize the data sender.
        
        Args:
            sensor: DummySensor instance for reading vital signs
            patient_id: ID of the patient being monitored
            server_url: Base URL for HTTP requests
            mqtt_broker: MQTT broker address
            mqtt_port: MQTT broker port
            mqtt_topic: MQTT topic for publishing
            protocol: Communication protocol ('mqtt' or 'http')
        """
        super().__init__()  # Call parent class constructor
        self.sensor = sensor
        self.patient_id = patient_id
        self.server_url = server_url
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic
        self.protocol = protocol.lower()
        self.mqtt_client = None
        
        if self.protocol == "mqtt":
            self._setup_mqtt()
        elif self.protocol != "http":
            raise ValueError("Protocol must be either 'mqtt' or 'http'")
    
    def _setup_mqtt(self) -> None:
        """Set up MQTT client connection."""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port)
            self.mqtt_client.loop_start()
            logging.info(f"Successfully connected to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}")
        except Exception as e:
            logging.error(f"Failed to connect to MQTT broker: {e}")
            self.mqtt_client = None
    
    def _send_data(self, data: Dict[str, Any]) -> bool:
        """
        Send data using the configured protocol.
        
        Args:
            data: Data to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.protocol == "mqtt":
            return self._send_mqtt(data)
        return self._send_http(data)
    
    def _send_http(self, data: Dict[str, Any]) -> bool:
        """
        Send data via HTTP POST request.
        
        Args:
            data: Data to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.server_url}/vital_signs",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            return response.status_code == 200
        except Exception as e:
            logging.error(f"HTTP send error: {e}")
            return False
    
    def _send_mqtt(self, data: Dict[str, Any]) -> bool:
        """
        Send data via MQTT.
        
        Args:
            data: Data to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.mqtt_client.publish(
                self.mqtt_topic,
                json.dumps(data),
                qos=1
            )
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logging.error(f"MQTT send error: {e}")
            return False
    
    def _convert_to_vital_signs(self, readings: Dict[str, SensorReading]) -> VitalSigns:
        """
        Convert sensor readings to VitalSigns object.
        
        Args:
            readings: Dictionary of sensor readings
            
        Returns:
            VitalSigns: Converted vital signs data
        """
        return VitalSigns(
            heart_rate=readings['heart_rate'].value,
            temperature=readings['temperature'].value,
            spo2=readings['spo2'].value,
            respiratory_rate=readings['respiratory_rate'].value,
            systolic_bp=readings['systolic_bp'].value,
            diastolic_bp=readings['diastolic_bp'].value,
            timestamp=datetime.now(),
            patient_id=self.patient_id,
            age=0  # Age should be configured based on patient data
        )
    
    def get_data(self) -> List[VitalSigns]:
        """
        Get vital signs data from the sensor.
        Implements the DataSource interface.
        
        Returns:
            List[VitalSigns]: List of vital signs readings
        """
        try:
            # Read all vital signs
            readings = self.sensor.read_all_vital_signs()
            
            # Convert to VitalSigns object
            vital_signs = self._convert_to_vital_signs(readings)
            
            # Send data to main system if connection is available
            if self.protocol == "mqtt" and self.mqtt_client is not None:
                self._send_data(asdict(vital_signs))
            elif self.protocol == "http":
                self._send_data(asdict(vital_signs))
            
            return [vital_signs]
            
        except Exception as e:
            logging.error(f"Error getting sensor data: {e}")
            return []
    
    def close(self) -> None:
        """Clean up resources."""
        if self.protocol == "mqtt" and self.mqtt_client is not None:
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logging.info("MQTT client disconnected")
            except Exception as e:
                logging.error(f"Error disconnecting MQTT client: {e}") 
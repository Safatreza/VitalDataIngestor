print("main2.py script started")

"""
Main entry point for the Vital Signs Monitoring System.

This module provides the command-line interface for various operations:
- Monitoring vital signs from different data sources
- Generating mock data for testing
- Running the visualization dashboard
- Predicting future vital signs using machine learning
- Raspberry Pi sensor integration
"""

import argparse
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, NoReturn
import pandas as pd
import logging

from src.data.vital_data_ingestor import (
    VitalDataIngestor,
    CSVDataSource,
    APIDataSource,
    SimulatedStreamDataSource
)
from src.analysis.anomaly_detector import AnomalyDetector
from src.analysis.baseline_comparator import BaselineComparator
from src.visualization.dashboard import VitalSignsDashboard
from src.analysis.vital_signs_predictor import VitalSignsPredictor
from src.utils.mock_data_generator import MockDataGenerator
from src.raspberry_pi.pi_data_sender import PiDataSender
from src.raspberry_pi.dummy_sensor import DummySensor

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(description='Vital Signs Monitoring System')
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    
    # Monitor mode
    monitor_parser = subparsers.add_parser('monitor', help='Monitor vital signs')
    monitor_parser.add_argument('--csv', help='Path to CSV file')
    monitor_parser.add_argument('--api-url', help='API endpoint URL')
    monitor_parser.add_argument('--interval', type=int, default=5,
                              help='Interval for simulated data (seconds)')
    monitor_parser.add_argument('--pi', action='store_true',
                              help='Enable Raspberry Pi monitoring')
    monitor_parser.add_argument('--mqtt-broker', help='MQTT broker address')
    monitor_parser.add_argument('--mqtt-port', type=int, default=1883,
                              help='MQTT broker port')
    monitor_parser.add_argument('--mqtt-topic', default='vital_signs',
                              help='MQTT topic for vital signs')
    
    # Generate mode
    generate_parser = subparsers.add_parser('generate', help='Generate mock data')
    generate_parser.add_argument('--patients', type=int, default=5,
                               help='Number of patients')
    generate_parser.add_argument('--hours', type=int, default=24,
                               help='Duration in hours')
    generate_parser.add_argument('--output', default='mock_vital_signs.csv',
                               help='Output file')
    generate_parser.add_argument('--abnormal-probability', type=float, default=0.2,
                               help='Probability of abnormal vital signs')
    
    # Dashboard mode
    subparsers.add_parser('dashboard', help='Run the dashboard')
    
    # Predict mode
    predict_parser = subparsers.add_parser('predict', help='Predict vital signs')
    predict_parser.add_argument('--input', required=True,
                              help='Input CSV file with historical data')
    predict_parser.add_argument('--model', default='vital_signs_model.h5',
                              help='Path to save/load the model')
    predict_parser.add_argument('--patient-id', help='Specific patient ID to predict for')
    predict_parser.add_argument('--days', type=int, default=7,
                              help='Number of days to plot')
    
    return parser

def print_vital_signs(vital_signs: Any) -> None:
    """
    Print vital signs data in a formatted way.
    
    Args:
        vital_signs: Vital signs data to print
    """
    print("\nVital Signs:")
    print(f"Patient ID: {vital_signs.patient_id}")
    print(f"Timestamp: {vital_signs.timestamp}")
    print(f"Heart Rate: {vital_signs.heart_rate} bpm")
    print(f"Temperature: {vital_signs.temperature}°C")
    print(f"SpO2: {vital_signs.spo2}%")
    print(f"Respiratory Rate: {vital_signs.respiratory_rate} bpm")
    print(f"Blood Pressure: {vital_signs.systolic_bp}/{vital_signs.diastolic_bp} mmHg")

def print_alerts(alerts: List[Any]) -> None:
    """
    Print alerts in a formatted way.
    
    Args:
        alerts: List of alerts to print
    """
    if alerts:
        print("\nAlerts:")
        for alert in alerts:
            print(f"- {alert.vital_sign}: {alert.message} ({alert.severity})")

def print_anomaly(anomaly: Any) -> None:
    """
    Print anomaly information in a formatted way.
    
    Args:
        anomaly: Anomaly data to print
    """
    if anomaly and anomaly.is_anomaly:
        print("\nAnomaly Detected!")
        print(f"Confidence: {anomaly.confidence:.2f}")
        print(f"Details: {anomaly.details}")

def run_monitor_mode(args: argparse.Namespace) -> None:
    """
    Run the monitoring mode.
    
    Args:
        args: Command line arguments for monitor mode
    """
    print("Entering run_monitor_mode...")
    ingestor = VitalDataIngestor()
    
    if args.csv:
        ingestor.add_data_source(CSVDataSource(args.csv))
    
    if args.api_url:
        ingestor.add_data_source(APIDataSource(args.api_url))
    
    if args.pi:
        if not args.mqtt_broker:
            logging.error("Error: MQTT broker address is required for Raspberry Pi monitoring")
            sys.exit(1)
            
        # Initialize DummySensor and PiDataSender with MQTT configuration
        sensor = DummySensor()
        pi_sender = PiDataSender(
            sensor=sensor,
            mqtt_broker=args.mqtt_broker,
            mqtt_port=args.mqtt_port,
            mqtt_topic=args.mqtt_topic,
            protocol="mqtt"  # Explicitly set protocol to MQTT
        )
        ingestor.add_data_source(pi_sender)
    else:
        ingestor.add_data_source(SimulatedStreamDataSource(interval=args.interval))
    
    try:
        while True:
            logging.debug("Monitor loop running...")
            vital_signs = ingestor.ingest_data()
            logging.debug(f"ingestor.ingest_data() returned: {vital_signs}")
            if vital_signs:
                print_vital_signs(vital_signs)
                analysis = ingestor.analyze_vital_signs(vital_signs)
                print_alerts(analysis.get('alerts', []))
                print_anomaly(analysis.get('anomaly_prediction'))
            else:
                logging.info("No vital signs data ingested this cycle.")
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    except Exception as e:
        logging.error(f"\nError during monitoring: {e}")
        sys.exit(1)

def run_generate_mode(args: argparse.Namespace) -> None:
    """
    Run the data generation mode.
    
    Args:
        args: Command line arguments for generate mode
    """
    try:
        generator = MockDataGenerator()
        generator.generate_dataset(
            num_patients=args.patients,
            start_time=datetime.now() - timedelta(hours=args.hours),
            duration_hours=args.hours,
            output_file=args.output
        )
        print(f"Generated mock data saved to {args.output}")
    except Exception as e:
        logging.error(f"Error generating data: {e}")
        sys.exit(1)

def run_predict_mode(args: argparse.Namespace) -> None:
    """
    Run the prediction mode.
    
    Args:
        args: Command line arguments for predict mode
    """
    try:
        predictor = VitalSignsPredictor(model_path=args.model)
        
        # Train the model if it doesn't exist
        if not predictor.model:
            logging.info("Training model...")
            predictor.train(args.input, validation_split=0.2)
            logging.info("Model training completed.")
        
        # Load data
        data = pd.read_csv(args.input)
        
        if args.patient_id:
            process_single_patient(predictor, data, args.patient_id, args.days)
        else:
            process_all_patients(predictor, data, args.days)
            
    except Exception as e:
        logging.error(f"Error during prediction: {e}")
        sys.exit(1)

def process_single_patient(predictor: VitalSignsPredictor, data: pd.DataFrame, 
                         patient_id: str, days: int) -> None:
    """
    Process predictions for a single patient.
    
    Args:
        predictor: VitalSignsPredictor instance
        data: DataFrame containing patient data
        patient_id: ID of the patient to process
        days: Number of days to plot
    """
    patient_data = data[data['patient_id'] == patient_id]
    if len(patient_data) == 0:
        logging.error(f"No data found for patient {patient_id}")
        return
    
    prediction = predictor.predict_next_day(patient_data)
    print(f"\nPredictions for patient {patient_id}:")
    for vital_sign, value in prediction.items():
        print(f"{vital_sign}: {value:.2f}")
    
    predictor.plot_predictions(patient_data, days_to_plot=days)
    print(f"\nPrediction plot saved to predictions.png")

def process_all_patients(predictor: VitalSignsPredictor, data: pd.DataFrame, 
                        days: int) -> None:
    """
    Process predictions for all patients.
    
    Args:
        predictor: VitalSignsPredictor instance
        data: DataFrame containing patient data
        days: Number of days to plot
    """
    for patient_id in data['patient_id'].unique():
        patient_data = data[data['patient_id'] == patient_id]
        prediction = predictor.predict_next_day(patient_data)
        print(f"\nPredictions for patient {patient_id}:")
        for vital_sign, value in prediction.items():
            print(f"{vital_sign}: {value:.2f}")
        
        predictor.plot_predictions(patient_data, days_to_plot=days)
        print(f"Prediction plot saved to predictions_{patient_id}.png")

def main() -> None:
    """
    Main entry point for the Vital Signs Monitoring System.
    Parses command line arguments and runs the appropriate mode.
    """
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        sys.exit(1)
    
    mode_handlers = {
        'monitor': run_monitor_mode,
        'generate': run_generate_mode,
        'dashboard': lambda _: VitalSignsDashboard().run(),
        'predict': run_predict_mode
    }
    
    try:
        mode_handlers[args.mode](args)
    except KeyError:
        logging.error("Invalid mode. Please use: monitor, generate, dashboard, or predict")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 
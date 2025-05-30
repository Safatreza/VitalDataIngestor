import argparse
from datetime import datetime, timedelta
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

def main():
    parser = argparse.ArgumentParser(description='Vital Signs Monitoring System')
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    
    # Monitor mode
    monitor_parser = subparsers.add_parser('monitor', help='Monitor vital signs')
    monitor_parser.add_argument('--csv', help='Path to CSV file')
    monitor_parser.add_argument('--api-url', help='API endpoint URL')
    monitor_parser.add_argument('--interval', type=int, default=5,
                              help='Interval for simulated data (seconds)')
    
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
    
    args = parser.parse_args()
    
    if args.mode == 'monitor':
        ingestor = VitalDataIngestor()
        
        if args.csv:
            ingestor.add_data_source(CSVDataSource(args.csv))
        
        if args.api_url:
            ingestor.add_data_source(APIDataSource(args.api_url))
        
        ingestor.add_data_source(SimulatedStreamDataSource(interval=args.interval))
        
        try:
            while True:
                vital_signs = ingestor.ingest_data()
                if vital_signs:
                    print("\nVital Signs:")
                    print(f"Patient ID: {vital_signs.patient_id}")
                    print(f"Timestamp: {vital_signs.timestamp}")
                    print(f"Heart Rate: {vital_signs.heart_rate} bpm")
                    print(f"Temperature: {vital_signs.temperature}°C")
                    print(f"SpO2: {vital_signs.spo2}%")
                    print(f"Respiratory Rate: {vital_signs.respiratory_rate} bpm")
                    print(f"Blood Pressure: {vital_signs.systolic_bp}/{vital_signs.diastolic_bp} mmHg")
                    
                    alerts = ingestor.analyze_vital_signs(vital_signs)
                    if alerts:
                        print("\nAlerts:")
                        for alert in alerts:
                            print(f"- {alert.vital_sign}: {alert.message} ({alert.severity})")
                    
                    anomaly = ingestor.detect_anomalies(vital_signs)
                    if anomaly and anomaly.is_anomaly:
                        print("\nAnomaly Detected!")
                        print(f"Confidence: {anomaly.confidence:.2f}")
                        print(f"Details: {anomaly.details}")
        
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
    
    elif args.mode == 'generate':
        generator = MockDataGenerator()
        generator.generate_dataset(
            num_patients=args.patients,
            start_time=datetime.now() - timedelta(hours=args.hours),
            duration_hours=args.hours,
            output_file=args.output
        )
        print(f"Generated mock data saved to {args.output}")
    
    elif args.mode == 'dashboard':
        dashboard = VitalSignsDashboard()
        dashboard.run()
    
    elif args.mode == 'predict':
        predictor = VitalSignsPredictor(model_path=args.model)
        
        # Train the model if it doesn't exist
        if not predictor.model:
            print("Training model...")
            predictor.train(args.input, validation_split=0.2)
            print("Model training completed.")
        
        # Load data
        import pandas as pd
        data = pd.read_csv(args.input)
        
        if args.patient_id:
            # Predict for specific patient
            patient_data = data[data['patient_id'] == args.patient_id]
            if len(patient_data) == 0:
                print(f"No data found for patient {args.patient_id}")
                return
            
            prediction = predictor.predict_next_day(patient_data)
            print(f"\nPredictions for patient {args.patient_id}:")
            for vital_sign, value in prediction.items():
                print(f"{vital_sign}: {value:.2f}")
            
            # Plot predictions
            predictor.plot_predictions(patient_data, days_to_plot=args.days)
            print(f"\nPrediction plot saved to predictions.png")
        
        else:
            # Predict for all patients
            for patient_id in data['patient_id'].unique():
                patient_data = data[data['patient_id'] == patient_id]
                prediction = predictor.predict_next_day(patient_data)
                print(f"\nPredictions for patient {patient_id}:")
                for vital_sign, value in prediction.items():
                    print(f"{vital_sign}: {value:.2f}")
                
                # Plot predictions
                predictor.plot_predictions(patient_data, days_to_plot=args.days)
                print(f"Prediction plot saved to predictions_{patient_id}.png")

if __name__ == '__main__':
    main() 
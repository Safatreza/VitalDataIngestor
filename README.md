# Vital Signs Monitoring System

A comprehensive system for monitoring, analyzing, and predicting patient vital signs using machine learning and real-time data processing.

## Features

- Real-time vital signs monitoring from multiple data sources (CSV, API, simulated stream)
- Anomaly detection using machine learning
- Baseline comparison for vital signs
- LSTM-based prediction of future vital signs
- Interactive dashboard for data visualization
- Mock data generation for testing and development

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/VitalDataIngestor.git
cd VitalDataIngestor
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Monitor Mode
Monitor vital signs in real-time:
```bash
python main.py monitor --csv data.csv --api-url http://api.example.com/vitals --interval 5
```

### Generate Mock Data
Generate mock vital signs data:
```bash
python main.py generate --patients 5 --hours 24 --output mock_data.csv
```

### Run Dashboard
Launch the interactive dashboard:
```bash
python main.py dashboard
```

### Predict Vital Signs
Train and use the LSTM model for vital signs prediction:
```bash
# Train model and predict for all patients
python main.py predict --input mock_data.csv

# Predict for a specific patient
python main.py predict --input mock_data.csv --patient-id 123

# Use a specific model file
python main.py predict --input mock_data.csv --model my_model.h5

# Plot more days
python main.py predict --input mock_data.csv --days 14
```

## Project Structure

```
VitalDataIngestor/
├── src/
│   ├── analysis/
│   │   ├── anomaly_detector.py
│   │   ├── baseline_comparator.py
│   │   └── vital_signs_predictor.py
│   ├── data/
│   │   ├── vital_data_ingestor.py
│   │   └── vital_data_storage.py
│   ├── utils/
│   │   └── mock_data_generator.py
│   └── visualization/
│       └── dashboard.py
├── tests/
│   ├── test_anomaly_detector.py
│   ├── test_baseline_comparator.py
│   ├── test_vital_data_ingestor.py
│   ├── test_vital_data_storage.py
│   └── test_vital_signs_predictor.py
├── main.py
├── requirements.txt
└── README.md
```

## Testing

Run the test suite:
```bash
python -m unittest discover tests
```

## Dependencies

- numpy>=1.21.0
- pandas>=1.3.0
- scikit-learn>=0.24.2
- joblib>=1.0.1
- requests>=2.26.0
- streamlit>=1.22.0
- plotly>=5.13.0
- tensorflow>=2.8.0
- matplotlib>=3.4.0

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
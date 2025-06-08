from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os
import logging

from src.data.data_sources import DataSource
from src.analysis.anomaly_detector import AnomalyDetector, AnomalyPrediction
from src.analysis.baseline_comparator import BaselineComparator, Alert
from src.data.models import VitalSigns

class VitalDataIngestor:
    """Main class for ingesting vital signs data from multiple sources."""
    
    def __init__(self, model_path: str = "anomaly_model.joblib"):
        """Initialize the ingestor with data sources and analyzers."""
        self.data_sources: List[DataSource] = []
        self.vital_signs_history: List[VitalSigns] = []
        self.anomaly_detector = AnomalyDetector(model_path=model_path)
        self.baseline_comparator = BaselineComparator()
        
        # Load baseline ranges
        try:
            self.baseline_comparator.load_baselines_from_json("baseline_ranges.json")
        except FileNotFoundError:
            logging.warning("Warning: baseline_ranges.json not found. Baseline comparison will not be available.")
        
        # Train anomaly detector if model doesn't exist
        if not os.path.exists(model_path):
            logging.info("Training anomaly detection model...")
            self.anomaly_detector.train_model(n_samples=1000)

    def add_data_source(self, source: DataSource) -> None:
        """Add a new data source to the ingestor."""
        self.data_sources.append(source)

    def ingest_data(self) -> List[Tuple[VitalSigns, List[Alert], Optional[AnomalyPrediction]]]:
        """Ingest data from all registered sources and analyze for anomalies."""
        results = []
        for source in self.data_sources:
            try:
                vital_signs_list = source.get_data()
                for vital_signs in vital_signs_list:
                    # Store in history
                    self.vital_signs_history.append(vital_signs)
                    
                    # Convert to dictionary for analysis
                    vital_signs_dict = vital_signs.to_dict()
                    
                    # Get baseline alerts
                    alerts = self.baseline_comparator.compare_vital_signs(
                        vital_signs_dict,
                        date_of_birth=datetime(1990, 1, 1),  # Default DOB, should be configurable
                        gender="M"  # Default gender, should be configurable
                    )
                    
                    # Get anomaly prediction
                    try:
                        prediction = self.anomaly_detector.predict(
                            vital_signs_dict,
                            vital_signs.timestamp
                        )
                    except Exception as e:
                        logging.error(f"Error in anomaly detection: {e}")
                        prediction = None
                    
                    results.append((vital_signs, alerts, prediction))
            except Exception as e:
                logging.error(f"Error ingesting data from source: {e}")
        
        return results

    def get_vital_signs_history(self) -> List[VitalSigns]:
        """Get the complete history of vital signs."""
        return self.vital_signs_history

    def clear_history(self) -> None:
        """Clear the vital signs history."""
        self.vital_signs_history.clear()

    def get_latest_vital_signs(self) -> Optional[VitalSigns]:
        """Get the most recent vital signs reading."""
        return self.vital_signs_history[-1] if self.vital_signs_history else None

    def analyze_vital_signs(self, vital_signs: VitalSigns) -> Tuple[List[Alert], Optional[AnomalyPrediction]]:
        """Analyze vital signs for both baseline alerts and anomalies."""
        vital_signs_dict = vital_signs.to_dict()
        
        # Get baseline alerts
        alerts = self.baseline_comparator.compare_vital_signs(
            vital_signs_dict,
            date_of_birth=datetime(1990, 1, 1),  # Default DOB, should be configurable
            gender="M"  # Default gender, should be configurable
        )
        
        # Get anomaly prediction
        try:
            prediction = self.anomaly_detector.predict(
                vital_signs_dict,
                vital_signs.timestamp
            )
        except Exception as e:
            logging.error(f"Error in anomaly detection: {e}")
            prediction = None
        
        return alerts, prediction 
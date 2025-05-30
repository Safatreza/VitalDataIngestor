import unittest
from datetime import datetime
from vital_data_ingestor import (
    VitalDataIngestor,
    VitalSigns,
    CSVDataSource,
    APIDataSource,
    SimulatedStreamDataSource
)

class TestVitalDataIngestor(unittest.TestCase):
    def setUp(self):
        self.ingestor = VitalDataIngestor()

    def test_vital_signs_validation(self):
        # Test valid vital signs
        valid_vitals = VitalSigns(
            heart_rate=75,
            temperature=36.8,
            spo2=98,
            respiratory_rate=16,
            systolic_bp=120,
            diastolic_bp=80,
            timestamp=datetime.now()
        )
        self.assertEqual(valid_vitals.heart_rate, 75)

        # Test invalid vital signs
        with self.assertRaises(ValueError):
            VitalSigns(
                heart_rate=250,  # Invalid heart rate
                temperature=36.8,
                spo2=98,
                respiratory_rate=16,
                systolic_bp=120,
                diastolic_bp=80,
                timestamp=datetime.now()
            )

    def test_simulated_stream(self):
        # Test simulated stream data source
        stream_source = SimulatedStreamDataSource(interval=0.1)
        self.ingestor.add_data_source(stream_source)
        
        # Ingest data multiple times
        for _ in range(3):
            vital_signs = self.ingestor.ingest_data()
            self.assertEqual(len(vital_signs), 1)
            
            # Verify vital signs are within valid ranges
            vital = vital_signs[0]
            self.assertTrue(40 <= vital.heart_rate <= 200)
            self.assertTrue(35 <= vital.temperature <= 42)
            self.assertTrue(70 <= vital.spo2 <= 100)
            self.assertTrue(8 <= vital.respiratory_rate <= 40)
            self.assertTrue(70 <= vital.systolic_bp <= 200)
            self.assertTrue(40 <= vital.diastolic_bp <= 120)

    def test_history_management(self):
        # Add simulated stream source
        stream_source = SimulatedStreamDataSource(interval=0.1)
        self.ingestor.add_data_source(stream_source)
        
        # Ingest data multiple times
        for _ in range(3):
            self.ingestor.ingest_data()
        
        # Verify history
        history = self.ingestor.get_vital_signs_history()
        self.assertEqual(len(history), 3)
        
        # Test latest vital signs
        latest = self.ingestor.get_latest_vital_signs()
        self.assertIsNotNone(latest)
        self.assertEqual(latest, history[-1])
        
        # Test clearing history
        self.ingestor.clear_history()
        self.assertEqual(len(self.ingestor.get_vital_signs_history()), 0)

if __name__ == '__main__':
    unittest.main() 
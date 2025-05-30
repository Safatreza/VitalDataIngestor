import unittest
from datetime import datetime, timedelta
import os
from vital_data_storage import VitalDataStorage, Patient

class TestVitalDataStorage(unittest.TestCase):
    def setUp(self):
        """Set up test database."""
        self.test_db_path = "test_vital_data.db"
        self.storage = VitalDataStorage(self.test_db_path)
        
        # Add a test patient
        self.patient_id = self.storage.add_patient(
            first_name="John",
            last_name="Doe",
            date_of_birth=datetime(1980, 1, 1),
            gender="M"
        )
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_add_and_get_patient(self):
        """Test adding and retrieving a patient."""
        patient = self.storage.get_patient(self.patient_id)
        self.assertIsNotNone(patient)
        self.assertEqual(patient.first_name, "John")
        self.assertEqual(patient.last_name, "Doe")
        self.assertEqual(patient.gender, "M")
    
    def test_store_and_get_vital_signs(self):
        """Test storing and retrieving vital signs."""
        # Store vital signs
        vital_signs = {
            'timestamp': datetime.now(),
            'heart_rate': 75.0,
            'temperature': 36.8,
            'spo2': 98.0,
            'respiratory_rate': 16.0,
            'systolic_bp': 120.0,
            'diastolic_bp': 80.0
        }
        
        record_id = self.storage.store_vital_signs(self.patient_id, vital_signs)
        self.assertIsNotNone(record_id)
        
        # Get latest vital signs
        latest = self.storage.get_latest_vital_signs(self.patient_id)
        self.assertIsNotNone(latest)
        self.assertEqual(latest['heart_rate'], 75.0)
        self.assertEqual(latest['temperature'], 36.8)
    
    def test_vital_signs_history(self):
        """Test retrieving vital signs history."""
        # Store multiple vital signs records
        base_time = datetime.now()
        for i in range(3):
            vital_signs = {
                'timestamp': base_time + timedelta(minutes=i),
                'heart_rate': 75.0 + i,
                'temperature': 36.8,
                'spo2': 98.0,
                'respiratory_rate': 16.0,
                'systolic_bp': 120.0,
                'diastolic_bp': 80.0
            }
            self.storage.store_vital_signs(self.patient_id, vital_signs)
        
        # Test getting all history
        history = self.storage.get_vital_signs_history(self.patient_id)
        self.assertEqual(len(history), 3)
        
        # Test getting history with time range
        start_time = base_time + timedelta(minutes=1)
        end_time = base_time + timedelta(minutes=2)
        filtered_history = self.storage.get_vital_signs_history(
            self.patient_id,
            start_time=start_time,
            end_time=end_time
        )
        self.assertEqual(len(filtered_history), 1)
        
        # Test getting history with limit
        limited_history = self.storage.get_vital_signs_history(
            self.patient_id,
            limit=2
        )
        self.assertEqual(len(limited_history), 2)
    
    def test_delete_patient_data(self):
        """Test deleting patient data."""
        # Store some vital signs
        vital_signs = {
            'timestamp': datetime.now(),
            'heart_rate': 75.0,
            'temperature': 36.8,
            'spo2': 98.0,
            'respiratory_rate': 16.0,
            'systolic_bp': 120.0,
            'diastolic_bp': 80.0
        }
        self.storage.store_vital_signs(self.patient_id, vital_signs)
        
        # Delete patient data
        self.storage.delete_patient_data(self.patient_id)
        
        # Verify data is deleted
        patient = self.storage.get_patient(self.patient_id)
        self.assertIsNone(patient)
        
        history = self.storage.get_vital_signs_history(self.patient_id)
        self.assertEqual(len(history), 0)

if __name__ == '__main__':
    unittest.main() 
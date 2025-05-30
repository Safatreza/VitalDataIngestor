import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from contextlib import contextmanager

@dataclass
class Patient:
    """Data class representing a patient."""
    id: int
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: str

class VitalDataStorage:
    """SQLite storage for patient vital signs data."""
    
    def __init__(self, db_path: str = "vital_data.db"):
        """Initialize the storage with the database path."""
        self.db_path = db_path
        self._create_tables()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable row factory for named columns
        try:
            yield conn
        finally:
            conn.close()
    
    def _create_tables(self) -> None:
        """Create the necessary database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create patients table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    date_of_birth DATE NOT NULL,
                    gender TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create vital_signs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vital_signs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    heart_rate REAL NOT NULL,
                    temperature REAL NOT NULL,
                    spo2 REAL NOT NULL,
                    respiratory_rate REAL NOT NULL,
                    systolic_bp REAL NOT NULL,
                    diastolic_bp REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id)
                )
            """)
            
            conn.commit()
    
    def add_patient(self, first_name: str, last_name: str, date_of_birth: datetime, gender: str) -> int:
        """Add a new patient to the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO patients (first_name, last_name, date_of_birth, gender)
                VALUES (?, ?, ?, ?)
            """, (first_name, last_name, date_of_birth.date().isoformat(), gender))
            conn.commit()
            return cursor.lastrowid
    
    def get_patient(self, patient_id: int) -> Optional[Patient]:
        """Retrieve a patient by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, first_name, last_name, date_of_birth, gender
                FROM patients
                WHERE id = ?
            """, (patient_id,))
            row = cursor.fetchone()
            
            if row:
                return Patient(
                    id=row['id'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    date_of_birth=datetime.fromisoformat(row['date_of_birth']),
                    gender=row['gender']
                )
            return None
    
    def store_vital_signs(self, patient_id: int, vital_signs: Dict[str, Any]) -> int:
        """Store vital signs data for a patient."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vital_signs (
                    patient_id, timestamp, heart_rate, temperature, spo2,
                    respiratory_rate, systolic_bp, diastolic_bp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id,
                vital_signs['timestamp'].isoformat(),
                vital_signs['heart_rate'],
                vital_signs['temperature'],
                vital_signs['spo2'],
                vital_signs['respiratory_rate'],
                vital_signs['systolic_bp'],
                vital_signs['diastolic_bp']
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_vital_signs_history(
        self,
        patient_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve vital signs history for a patient."""
        query = """
            SELECT timestamp, heart_rate, temperature, spo2,
                   respiratory_rate, systolic_bp, diastolic_bp
            FROM vital_signs
            WHERE patient_id = ?
        """
        params = [patient_id]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_latest_vital_signs(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """Get the most recent vital signs for a patient."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, heart_rate, temperature, spo2,
                       respiratory_rate, systolic_bp, diastolic_bp
                FROM vital_signs
                WHERE patient_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (patient_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def delete_patient_data(self, patient_id: int) -> None:
        """Delete all data for a patient."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vital_signs WHERE patient_id = ?", (patient_id,))
            cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            conn.commit() 
"""
Shunt300 Database Module
SQLite database for comprehensive data persistence:
- Device list management
- Historical sensor readings (time-series)
- Recording session management
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


class Shunt300Database:
    """SQLite database manager for Shunt300 data."""
    
    def __init__(self, db_path: str = "shunt300_data.db", verbose: bool = False):
        self.db_path = Path(db_path)
        self.verbose = verbose
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database and create tables if they don't exist."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Devices table (replaces device_list.json)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_connected TIMESTAMP,
                connection_count INTEGER DEFAULT 0,
                notes TEXT
            )
        """)
        
        # Sensor readings table (time-series data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_address TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                voltage REAL,
                current REAL,
                power REAL,
                soc REAL,
                energy REAL,
                status TEXT,
                starter_voltage REAL,
                temperature_1 REAL,
                temperature_2 REAL,
                temperature_3 REAL,
                sequence INTEGER,
                raw_data TEXT,
                FOREIGN KEY (device_address) REFERENCES devices(address)
            )
        """)
        
        # Recording sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recording_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_address TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                frame_count INTEGER DEFAULT 0,
                duration_seconds REAL,
                notes TEXT,
                FOREIGN KEY (device_address) REFERENCES devices(address)
            )
        """)
        
        # Recording frames table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recording_frames (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                frame_index INTEGER NOT NULL,
                captured_at TIMESTAMP NOT NULL,
                payload TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES recording_sessions(id) ON DELETE CASCADE
            )
        """)

        # App settings table (capacity + preferences)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_device_time ON sensor_readings(device_address, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recording_frames_session ON recording_frames(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_devices_address ON devices(address)")
        
        self.conn.commit()
        
        if self.verbose:
            print(f"✅ Database initialized: {self.db_path}")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    # ========== Device Management ==========
    
    def add_or_update_device(self, address: str, name: str) -> bool:
        """Add new device or update existing device's last_seen timestamp."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO devices (address, name, last_seen)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(address) DO UPDATE SET
                    name = excluded.name,
                    last_seen = CURRENT_TIMESTAMP
            """, (address, name))
            self.conn.commit()
            return True
        except Exception as e:
            if self.verbose:
                print(f"Error adding/updating device: {e}")
            return False
    
    def update_device_connection(self, address: str) -> bool:
        """Update device's last_connected timestamp and increment connection_count."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE devices 
                SET last_connected = CURRENT_TIMESTAMP,
                    connection_count = connection_count + 1
                WHERE address = ?
            """, (address,))
            self.conn.commit()
            return True
        except Exception as e:
            if self.verbose:
                print(f"Error updating device connection: {e}")
            return False
    
    def get_devices(self) -> List[Dict[str, Any]]:
        """Get all devices."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT address, name, first_seen, last_seen, last_connected, connection_count, notes
                FROM devices
                ORDER BY last_seen DESC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            if self.verbose:
                print(f"Error getting devices: {e}")
            return []
    
    def clear_devices(self) -> bool:
        """Clear all devices from database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM devices")
            self.conn.commit()
            return True
        except Exception as e:
            if self.verbose:
                print(f"Error clearing devices: {e}")
            return False
    
    # ========== Sensor Readings ==========
    
    def log_sensor_reading(self, device_address: str, reading: Dict[str, Any]) -> bool:
        """Log a sensor reading to the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO sensor_readings (
                    device_address, voltage, current, power, soc, energy, status,
                    starter_voltage, temperature_1, temperature_2, temperature_3,
                    sequence, raw_data
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                device_address,
                reading.get('voltage'),
                reading.get('current'),
                reading.get('power'),
                reading.get('soc'),
                reading.get('energy'),
                reading.get('status'),
                reading.get('starter_voltage'),
                reading.get('temperature_1'),
                reading.get('temperature_2'),
                reading.get('temperature_3'),
                reading.get('sequence'),
                json.dumps(reading)
            ))
            self.conn.commit()
            return True
        except Exception as e:
            if self.verbose:
                print(f"Error logging sensor reading: {e}")
            return False
    
    def get_sensor_readings(self, device_address: Optional[str] = None, 
                           limit: int = 100, 
                           start_time: Optional[str] = None,
                           end_time: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sensor readings with optional filters."""
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM sensor_readings WHERE 1=1"
            params = []
            
            if device_address:
                query += " AND device_address = ?"
                params.append(device_address)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            if self.verbose:
                print(f"Error getting sensor readings: {e}")
            return []
    
    def get_reading_statistics(self, device_address: str, 
                               hours: int = 24) -> Dict[str, Any]:
        """Get statistical summary of readings for a device."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as count,
                    AVG(voltage) as avg_voltage,
                    AVG(current) as avg_current,
                    AVG(power) as avg_power,
                    AVG(soc) as avg_soc,
                    MIN(soc) as min_soc,
                    MAX(soc) as max_soc,
                    MIN(timestamp) as first_reading,
                    MAX(timestamp) as last_reading
                FROM sensor_readings
                WHERE device_address = ?
                AND timestamp >= datetime('now', '-' || ? || ' hours')
            """, (device_address, hours))
            row = cursor.fetchone()
            return dict(row) if row else {}
        except Exception as e:
            if self.verbose:
                print(f"Error getting statistics: {e}")
            return {}
    
    def clear_old_readings(self, days: int = 30) -> int:
        """Clear sensor readings older than specified days. Returns count deleted."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM sensor_readings
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            """, (days,))
            deleted = cursor.rowcount
            self.conn.commit()
            return deleted
        except Exception as e:
            if self.verbose:
                print(f"Error clearing old readings: {e}")
            return 0
    
    # ========== Recording Sessions ==========
    
    def start_recording_session(self, device_address: Optional[str] = None, 
                                notes: Optional[str] = None) -> int:
        """Start a new recording session. Returns session_id."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO recording_sessions (device_address, notes)
                VALUES (?, ?)
            """, (device_address, notes))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            if self.verbose:
                print(f"Error starting recording session: {e}")
            return 0
    
    def end_recording_session(self, session_id: int) -> bool:
        """End a recording session and update metadata."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE recording_sessions
                SET end_time = CURRENT_TIMESTAMP,
                    duration_seconds = (
                        julianday(CURRENT_TIMESTAMP) - julianday(start_time)
                    ) * 86400,
                    frame_count = (
                        SELECT COUNT(*) FROM recording_frames WHERE session_id = ?
                    )
                WHERE id = ?
            """, (session_id, session_id))
            self.conn.commit()
            return True
        except Exception as e:
            if self.verbose:
                print(f"Error ending recording session: {e}")
            return False
    
    def add_recording_frame(self, session_id: int, frame_index: int, 
                           payload: Dict[str, Any], captured_at: str) -> bool:
        """Add a frame to a recording session."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO recording_frames (session_id, frame_index, captured_at, payload)
                VALUES (?, ?, ?, ?)
            """, (session_id, frame_index, captured_at, json.dumps(payload)))
            self.conn.commit()
            return True
        except Exception as e:
            if self.verbose:
                print(f"Error adding recording frame: {e}")
            return False
    
    def get_recording_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recording sessions."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, device_address, start_time, end_time, 
                       frame_count, duration_seconds, notes
                FROM recording_sessions
                ORDER BY start_time DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            if self.verbose:
                print(f"Error getting recording sessions: {e}")
            return []
    
    def get_recording_frames(self, session_id: int) -> List[Dict[str, Any]]:
        """Get all frames from a recording session."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT frame_index, captured_at, payload
                FROM recording_frames
                WHERE session_id = ?
                ORDER BY frame_index
            """, (session_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            if self.verbose:
                print(f"Error getting recording frames: {e}")
            return []
    
    def delete_recording_session(self, session_id: int) -> bool:
        """Delete a recording session and all its frames."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM recording_sessions WHERE id = ?", (session_id,))
            self.conn.commit()
            return True
        except Exception as e:
            if self.verbose:
                print(f"Error deleting recording session: {e}")
            return False

    # ========== App Settings ==========

    def set_setting(self, key: str, value: Any) -> bool:
        """Set an app setting value as text."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (key, str(value))
            )
            self.conn.commit()
            return True
        except Exception as e:
            if self.verbose:
                print(f"Error setting app setting '{key}': {e}")
            return False

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get an app setting value as text."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row is None:
                return default
            return row[0]
        except Exception as e:
            if self.verbose:
                print(f"Error getting app setting '{key}': {e}")
            return default
    
    # ========== Utility Methods ==========
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM devices")
            device_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as count FROM sensor_readings")
            reading_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as count FROM recording_sessions")
            session_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as count FROM recording_frames")
            frame_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) as count FROM app_settings")
            setting_count = cursor.fetchone()[0]
            
            # Get database file size
            db_size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0
            db_size_mb = round(db_size_bytes / (1024 * 1024), 2)
            
            return {
                'device_count': device_count,
                'reading_count': reading_count,
                'session_count': session_count,
                'frame_count': frame_count,
                'setting_count': setting_count,
                'database_size_mb': db_size_mb,
                'database_path': str(self.db_path)
            }
        except Exception as e:
            if self.verbose:
                print(f"Error getting database stats: {e}")
            return {}
    
    def vacuum(self) -> bool:
        """Optimize database by running VACUUM."""
        try:
            self.conn.execute("VACUUM")
            return True
        except Exception as e:
            if self.verbose:
                print(f"Error vacuuming database: {e}")
            return False

    def purge_all_data(self) -> bool:
        """Delete all data from all tables (for clean distribution)."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM recording_frames")
            cursor.execute("DELETE FROM recording_sessions")
            cursor.execute("DELETE FROM sensor_readings")
            cursor.execute("DELETE FROM devices")
            cursor.execute("DELETE FROM app_settings")
            self.conn.commit()
            self.conn.execute("VACUUM")

            if self.verbose:
                print("✅ Database purged: All data deleted")
            return True
        except Exception as e:
            if self.verbose:
                print(f"Error purging database: {e}")
            return False

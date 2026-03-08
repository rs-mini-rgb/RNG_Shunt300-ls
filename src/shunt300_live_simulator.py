"""
Shunt300 Live Simulator - Standalone Package
Connects directly to Renogy Shunt300 (RTMShunt) via BLE and serves real-time web interface.

This version maintains a persistent BLE connection and streams data live
without requiring log files or separate capture scripts.

Features:
- Automatic RTMShunt device discovery
- Persistent device list (SQLite database)
- Historical sensor data logging
- Recording session management
- Manual MAC address entry
- No RSSI monitoring (Windows limitation)
- Clean device cache management
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

try:
    import pystray
    from PIL import Image
except ImportError:
    pystray = None
    Image = None

try:
    from bleak import BleakClient
    from bleak import BleakScanner
except ImportError:
    print("ERROR: bleak library not installed. Run: pip install bleak")
    sys.exit(1)

try:
    from shunt300_database import Shunt300Database
    USE_DATABASE = True
except ImportError:
    print("⚠️  Database module not found. Using JSON fallback for device list.")
    USE_DATABASE = False


# Known notification UUID for Renogy Shunt300
SHUNT_NOTIFY_UUID = "0000c411-0000-1000-8000-00805f9b34fb"
FALLBACK_NOTIFY_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"

# Device list persistence file
DEVICE_LIST_FILE = "device_list.json"

# Capacity limits derived from Shunt 300 spec:
# 1-6500Ah and 8-120V => 0.008kWh to 780kWh
MIN_CAPACITY_KWH = 0.008
MAX_CAPACITY_KWH = 780.0


def get_app_dir() -> Path:
    """Return runtime application directory for source and bundled executable."""
    if getattr(sys, 'frozen', False):
        # PyInstaller: use executable parent for DB, but _MEIPASS for bundled files
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_resource_dir() -> Path:
    """Return directory where bundled resource files (HTML, images) are located."""
    if getattr(sys, 'frozen', False):
        # PyInstaller one-file: _MEIPASS temp directory
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            meipass_path = Path(meipass).resolve()
            if meipass_path.exists():
                return meipass_path

        # PyInstaller one-dir: bundled files are typically under _internal
        exe_parent = Path(sys.executable).resolve().parent
        internal_dir = exe_parent / '_internal'
        if internal_dir.exists():
            return internal_dir

        return exe_parent
    return Path(__file__).resolve().parent


def resolve_resource_path(relative_path: str) -> Path:
    """Resolve resource path across frozen/dev and legacy/current install layouts.

    Ensures that the resolved path stays within the RESOURCE_DIR tree to avoid
    serving files from unintended locations when given untrusted input.
    """
    candidates = [
        RESOURCE_DIR / relative_path,
        APP_DIR / '_internal' / relative_path,
        APP_DIR / relative_path,
    ]

    script_dir = Path(__file__).resolve().parent
    candidates.extend([
        script_dir / relative_path,
        script_dir / '_internal' / relative_path,
    ])

    # Resolve RESOURCE_DIR once to a canonical path so that symlinks and
    # non-normalized components do not defeat the ancestry check below.
    # If RESOURCE_DIR itself cannot be resolved (e.g. it does not exist yet),
    # no candidate will pass resolved.exists(), so falling back to the
    # unresolved value is safe: the loop will find no valid candidate and we
    # return the guaranteed-nonexistent path below.
    try:
        resource_root = RESOURCE_DIR.resolve()
    except OSError:
        resource_root = RESOURCE_DIR

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            # If the path cannot be resolved (for example, due to invalid
            # components), skip this candidate.
            continue

        # Only allow files that exist and are located within RESOURCE_DIR
        if resolved.exists() and (resolved == resource_root or resource_root in resolved.parents):
            return resolved

    # Fall back to a guaranteed-under-RESOURCE_DIR, intentionally invalid path.
    # Callers that check .exists() will treat this as a missing resource (404),
    # but we no longer risk returning a path that escapes RESOURCE_DIR.
    return RESOURCE_DIR / "__invalid_resource__" / relative_path


def get_data_dir() -> Path:
    """Return user-writable directory for database and persistent data.
    
    Uses LOCALAPPDATA on Windows for installed apps to avoid permission issues
    in Program Files. For development mode, uses the script directory.
    """
    if getattr(sys, 'frozen', False):
        # Installed app: use user's local app data folder
        if os.name == 'nt':  # Windows
            appdata = os.getenv('LOCALAPPDATA', os.path.expanduser('~'))
            data_dir = Path(appdata) / 'Shunt300LiveSimulator'
        else:  # Linux/Mac
            data_dir = Path.home() / '.local' / 'share' / 'Shunt300LiveSimulator'
        
        # Create directory if it doesn't exist
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    else:
        # Development mode: use script directory
        return Path(__file__).resolve().parent


APP_DIR = get_app_dir()
RESOURCE_DIR = get_resource_dir()
DATA_DIR = get_data_dir()


class Shunt300LiveSimulator:
    """Live BLE connection with HTTP server for web UI."""
    
    def __init__(self, mac: str, estimate_capacity_kwh: float = 0.0, verbose: bool = False, auto_connect: bool = False, enable_db_logging: bool = True, open_browser: bool = True, enable_tray: bool = True):
        self.mac = mac
        self.app_dir = APP_DIR
        self.estimate_capacity_kwh = estimate_capacity_kwh
        self.verbose = verbose
        self.auto_connect = auto_connect
        self.enable_db_logging = enable_db_logging
        self.open_browser = open_browser
        self.enable_tray = enable_tray
        self.running = False
        self.host = '127.0.0.1'
        self.port = 8081
        self.http_server = None
        self.tray_icon = None
        self.client = None
        self.reconnect_requested = False
        self.reconnect_reason = None
        self.last_reconnect_reason = 'none'
        self.reconnect_count = 0
        self.manual_disconnect = False if auto_connect else True
        self.stale_after_seconds = 20
        self.stale_reconnect_cooldown_seconds = 45
        self.min_connected_before_stale_check_seconds = 20
        self.last_connect_time = None
        self.last_reconnect_attempt_time = 0.0
        self.last_reconnect_at = None
        self.packet_rate_per_sec = 0.0
        self.last_rate_calc_time = time.time()
        self.last_rate_calc_count = 0
        
        # Initialize database if available
        self.db = None
        if USE_DATABASE and enable_db_logging:
            try:
                db_path = DATA_DIR / 'shunt300_data.db'
                self.db = Shunt300Database(db_path=str(db_path), verbose=verbose)
                if verbose:
                    stats = self.db.get_database_stats()
                    print(f"📊 Database: {stats['reading_count']} readings, {stats['device_count']} devices, {stats['database_size_mb']} MB")
            except Exception as e:
                print(f"⚠️  Database initialization failed: {e}")
                self.db = None

        # Load persisted capacity only after user explicitly sets it in UI at least once.
        # This keeps first-run behavior at 0.0 even if legacy test values exist in DB.
        if self.db:
            if self.estimate_capacity_kwh <= 0:
                user_set_flag = (self.db.get_setting('capacity_user_set', 'false') or 'false').strip().lower()
                if user_set_flag in ('true', '1', 'yes', 'on'):
                    persisted_capacity = self.db.get_setting('capacity_kwh')
                    if persisted_capacity is not None:
                        try:
                            parsed_capacity = round(float(persisted_capacity), 3)
                            if parsed_capacity > 0:
                                self.estimate_capacity_kwh = parsed_capacity
                                if self.verbose:
                                    print(f"🔁 Loaded saved capacity: {self.estimate_capacity_kwh} kWh")
                        except (TypeError, ValueError):
                            pass
        
        # Latest sensor data (shared between BLE thread and HTTP server)
        self.latest_data = {
            'voltage': None,
            'current': None,
            'power': None,
            'soc': None,
            'energy': None,
            'estimated_energy_kwh': None,
            'energy_source': 'unknown',
            'starter_voltage': None,
            'temperature_1': None,
            'temperature_2': None,
            'temperature_3': None,
            'hist_value_1': None,
            'hist_value_2': None,
            'hint_value_3': None,
            'hist_value_4': None,
            'hist_value_5': None,
            'hist_value_6': None,
            'additional_value': None,
            'sequence': None,
            'status': 'unknown',
            'confidence': 'unknown',
            'verified': False,
            'raw_payload': None,
            'timestamp': None,
            'connected': False,
            'notification_count': 0,
            'last_update_age_sec': None,
            'last_update_age_text': 'waiting for data...',
            'connection_status': 'disconnected',
            'packet_rate_per_sec': 0.0,
            'reconnect_count': 0,
            'last_reconnect_reason': 'none',
            'last_reconnect_at': None,
            'reconnect_cooldown_remaining_sec': 0,
            'connected_for_sec': None,
            'connected_for_text': 'n/a',
            'configured_capacity_kwh': self.estimate_capacity_kwh,
            'current_device_name': None,
            'current_device_mac': None,
        }
        self.data_lock = threading.Lock()
        self.last_update_time = None
        
    def bytes_to_int(self, data: bytes, offset: int, length: int, signed: bool = False, scale: float = 1.0) -> float:
        """Extract integer from bytes and apply scale."""
        if len(data) < offset + length:
            return 0.0
        value = int.from_bytes(data[offset: offset + length], byteorder="big", signed=signed)
        return round(value * scale, 3)
    
    def parse_bw_packet(self, data: bytes) -> Optional[dict]:
        """Parse 110-byte BW notification packet from Shunt300."""
        if len(data) < 110:
            return None
        if data[0:2] != b"BW":
            return None
        
        sequence = int.from_bytes(data[2:4], byteorder="big", signed=False)
        battery_voltage = self.bytes_to_int(data, 25, 3, scale=0.001)
        battery_current = self.bytes_to_int(data, 21, 3, signed=True, scale=0.001)
        starter_voltage = self.bytes_to_int(data, 30, 2, scale=0.001)
        state_of_charge = self.bytes_to_int(data, 34, 2, scale=0.1)
        power = round(battery_voltage * battery_current, 2)
        
        # Extended sensors
        temperature_1 = self.bytes_to_int(data, 72, 2, scale=0.001)
        temperature_2 = self.bytes_to_int(data, 76, 2, scale=0.001)
        temperature_3 = self.bytes_to_int(data, 80, 2, scale=0.001)
        hist_value_1 = self.bytes_to_int(data, 84, 2, scale=0.001)
        hist_value_2 = self.bytes_to_int(data, 88, 2, scale=0.001)
        hist_value_3 = self.bytes_to_int(data, 92, 2, scale=0.001)
        hist_value_4 = self.bytes_to_int(data, 96, 2, scale=0.001)
        hist_value_5 = self.bytes_to_int(data, 100, 2, scale=0.001)
        hist_value_6 = self.bytes_to_int(data, 104, 2, scale=0.001)
        additional_value = self.bytes_to_int(data, 108, 2, scale=0.001)
        
        return {
            "sequence": sequence,
            "voltage": battery_voltage,
            "current": battery_current,
            "starter_voltage": starter_voltage,
            "soc": state_of_charge,
            "power": power,
            "temperature_1": temperature_1,
            "temperature_2": temperature_2,
            "temperature_3": temperature_3,
            "hist_value_1": hist_value_1,
            "hist_value_2": hist_value_2,
            "hist_value_3": hist_value_3,
            "hist_value_4": hist_value_4,
            "hist_value_5": hist_value_5,
            "hist_value_6": hist_value_6,
            "additional_value": additional_value,
        }
    
    def derive_status(self, current: float) -> str:
        """Derive battery status from current value."""
        # Fixed logic: negative current = discharging
        if current < -0.05:
            return "discharging"
        elif current > 0.05:
            return "charging"
        else:
            return "idle"
    
    def format_age(self, seconds: float) -> str:
        """Format age in human-readable text."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
    
    def notification_handler(self, sender: int, data: bytearray) -> None:
        """Handle incoming BLE notifications."""
        try:
            parsed = self.parse_bw_packet(bytes(data))
            if not parsed:
                return
            
            with self.data_lock:
                # Update all sensor values
                for key in ['voltage', 'current', 'power', 'soc', 'starter_voltage',
                           'temperature_1', 'temperature_2', 'temperature_3',
                           'hist_value_1', 'hist_value_2', 'hist_value_3',
                           'hist_value_4', 'hist_value_5', 'hist_value_6',
                           'additional_value', 'sequence']:
                    if key in parsed:
                        self.latest_data[key] = parsed[key]
                
                # Update diagnostic sensors
                self.latest_data['confidence'] = 'verified'
                self.latest_data['verified'] = True
                self.latest_data['raw_payload'] = bytes(data).hex()
                
                # Derive status from current
                self.latest_data['status'] = self.derive_status(parsed['current'])
                
                # Energy estimation from SOC
                if parsed['soc'] is not None:
                    if self.estimate_capacity_kwh > 0:
                        self.latest_data['estimated_energy_kwh'] = round(
                            (parsed['soc'] / 100.0) * self.estimate_capacity_kwh, 3
                        )
                        self.latest_data['energy_source'] = f"estimated_soc_capacity_{self.estimate_capacity_kwh}kWh"
                    else:
                        self.latest_data['estimated_energy_kwh'] = None
                        self.latest_data['energy_source'] = 'capacity_not_set'
                
                self.latest_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.latest_data['notification_count'] += 1
                self.latest_data['connection_status'] = 'connected'
                self.last_update_time = time.time()
                self.reconnect_requested = False
                self.reconnect_reason = None
                
                # Log to database every 10 readings to reduce overhead
                if self.db and self.latest_data['notification_count'] % 10 == 0:
                    reading_data = {
                        'voltage': self.latest_data['voltage'],
                        'current': self.latest_data['current'],
                        'power': self.latest_data['power'],
                        'soc': self.latest_data['soc'],
                        'energy': self.latest_data['estimated_energy_kwh'],
                        'status': self.latest_data['status'],
                        'starter_voltage': self.latest_data['starter_voltage'],
                        'temperature_1': self.latest_data['temperature_1'],
                        'temperature_2': self.latest_data['temperature_2'],
                        'temperature_3': self.latest_data['temperature_3'],
                        'sequence': self.latest_data['sequence'],
                    }
                    self.db.log_sensor_reading(self.mac, reading_data)
                
                if self.verbose and self.latest_data['notification_count'] % 10 == 0:
                    print(f"[{self.latest_data['timestamp']}] "
                          f"Updates: {self.latest_data['notification_count']}, "
                          f"Status: {self.latest_data['status']}, "
                          f"SOC: {self.latest_data['soc']}%, "
                          f"Current: {self.latest_data['current']}A")
        
        except Exception as e:
            print(f"Error in notification handler: {e}")

    async def request_reconnect(self, reason: str = 'manual') -> None:
        """Request BLE reconnect and drop current connection if active."""
        now = time.time()
        if reason == 'stale_stream' and (now - self.last_reconnect_attempt_time) < self.stale_reconnect_cooldown_seconds:
            return

        self.last_reconnect_attempt_time = now
        self.manual_disconnect = False
        self.reconnect_requested = True
        self.reconnect_reason = reason
        self.last_reconnect_reason = reason
        self.last_reconnect_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.reconnect_count += 1
        with self.data_lock:
            self.latest_data['connection_status'] = f'reconnecting ({reason})'
            self.latest_data['reconnect_count'] = self.reconnect_count
            self.latest_data['last_reconnect_reason'] = self.last_reconnect_reason
            self.latest_data['last_reconnect_at'] = self.last_reconnect_at

        if self.client and self.client.is_connected:
            try:
                await self.client.disconnect()
            except Exception:
                pass

    async def connect(self) -> None:
        """Request normal connection without counting as reconnect."""
        self.manual_disconnect = False
        self.reconnect_requested = False
        self.reconnect_reason = None

        with self.data_lock:
            if self.client and self.client.is_connected:
                self.latest_data['connected'] = True
                self.latest_data['connection_status'] = 'connected'
            else:
                self.latest_data['connection_status'] = 'connecting'

    async def disconnect(self) -> None:
        """Disconnect from BLE device without reconnecting."""
        self.manual_disconnect = True
        self.reconnect_requested = False
        self.reconnect_reason = None
        with self.data_lock:
            self.latest_data['connection_status'] = 'disconnected (manual)'
            self.latest_data['connected'] = False
        
        if self.client and self.client.is_connected:
            try:
                await self.client.disconnect()
            except Exception:
                pass

    def reset_counters(self) -> None:
        """Reset UI-visible counters and clear sensor data."""
        with self.data_lock:
            # Reset counters
            self.latest_data['notification_count'] = 0
            self.latest_data['reconnect_count'] = 0
            self.latest_data['last_reconnect_reason'] = 'none'
            
            # Clear sensor data
            self.latest_data['voltage'] = None
            self.latest_data['current'] = None
            self.latest_data['power'] = None
            self.latest_data['soc'] = None
            self.latest_data['energy'] = None
            self.latest_data['estimated_energy_kwh'] = None
            self.latest_data['status'] = 'unknown'
            
            # Clear diagnostic data
            self.latest_data['confidence'] = 'unknown'
            self.latest_data['verified'] = False
            self.latest_data['raw_payload'] = None
            
            # Clear extended sensors
            self.latest_data['starter_voltage'] = None
            self.latest_data['temperature_1'] = None
            self.latest_data['temperature_2'] = None
            self.latest_data['temperature_3'] = None
            self.latest_data['hist_value_1'] = None
            self.latest_data['hist_value_2'] = None
            self.latest_data['hist_value_3'] = None
            self.latest_data['hist_value_4'] = None
            self.latest_data['hist_value_5'] = None
            self.latest_data['hist_value_6'] = None
            self.latest_data['additional_value'] = None
            self.latest_data['sequence'] = None
            
            # Reset timestamps and age
            self.latest_data['timestamp'] = None
            self.latest_data['last_update_age_sec'] = None
            self.latest_data['last_update_age_text'] = 'waiting for data...'
            self.latest_data['last_reconnect_at'] = None
            self.latest_data['reconnect_cooldown_remaining_sec'] = 0
            self.latest_data['connected_for_sec'] = None
            self.latest_data['connected_for_text'] = 'n/a'
            
        self.reconnect_count = 0
        self.last_reconnect_reason = 'none'
        self.last_reconnect_at = None
        self.last_reconnect_attempt_time = 0.0
        self.last_rate_calc_count = 0
        self.last_rate_calc_time = time.time()
        self.last_update_time = None

    def set_capacity(self, capacity_kwh) -> dict:
        """Set battery capacity used for SOC-based energy estimation."""
        try:
            capacity_value = float(capacity_kwh)
        except (TypeError, ValueError):
            return {'success': False, 'message': 'Invalid capacity value'}

        if capacity_value < MIN_CAPACITY_KWH:
            return {'success': False, 'message': f'Capacity too low (min {MIN_CAPACITY_KWH} kWh)'}

        if capacity_value > MAX_CAPACITY_KWH:
            return {'success': False, 'message': f'Capacity too large (max {MAX_CAPACITY_KWH} kWh)'}

        capacity_value = round(capacity_value, 3)
        self.estimate_capacity_kwh = capacity_value

        if self.db:
            self.db.set_setting('capacity_kwh', capacity_value)
            self.db.set_setting('capacity_user_set', 'true')

        with self.data_lock:
            self.latest_data['configured_capacity_kwh'] = capacity_value
            soc = self.latest_data.get('soc')
            if soc is not None:
                self.latest_data['estimated_energy_kwh'] = round((soc / 100.0) * capacity_value, 3)
                self.latest_data['energy_source'] = f"estimated_soc_capacity_{capacity_value}kWh"

        return {
            'success': True,
            'message': f'Capacity set to {capacity_value} kWh',
            'capacity_kwh': capacity_value,
            'estimated_energy_kwh': self.latest_data.get('estimated_energy_kwh')
        }

    @staticmethod
    def _normalize_mac(value: str) -> str:
        return (value or '').replace('-', ':').upper().strip()

    def load_device_list(self) -> list:
        """Load saved device list from database or JSON file."""
        # Try database first
        if self.db:
            devices = self.db.get_devices()
            # Convert to format expected by UI
            return [
                {
                    'address': d['address'],
                    'name': d['name'],
                    'last_seen': d['last_seen']
                }
                for d in devices
            ]
        
        # Fallback to JSON
        device_list_path = DATA_DIR / DEVICE_LIST_FILE
        if device_list_path.exists():
            try:
                with open(device_list_path, 'r') as f:
                    return json.load(f)
            except Exception as exc:
                if self.verbose:
                    print(f"Failed to load device list: {exc}")
        return []

    def save_device_list(self, devices: list) -> bool:
        """Save device list to database or JSON file."""
        # Try database first
        if self.db:
            success = True
            for device in devices:
                if not self.db.add_or_update_device(device['address'], device['name']):
                    success = False
            return success
        
        # Fallback to JSON
        device_list_path = DATA_DIR / DEVICE_LIST_FILE
        try:
            with open(device_list_path, 'w') as f:
                json.dump(devices, f, indent=2)
            return True
        except Exception as exc:
            if self.verbose:
                print(f"Failed to save device list: {exc}")
            return False

    def clear_device_list(self) -> bool:
        """Clear the device list from database or JSON file."""
        # Try database first
        if self.db:
            return self.db.clear_devices()
        
        # Fallback to JSON
        device_list_path = DATA_DIR / DEVICE_LIST_FILE
        try:
            if device_list_path.exists():
                device_list_path.unlink()
            return True
        except Exception as exc:
            if self.verbose:
                print(f"Failed to clear device list: {exc}")
            return False

    def _extract_device_info(self, device) -> dict:
        """Extract name and address from a BLE device object."""
        address = getattr(device, 'address', 'Unknown')
        
        # Get device name - try multiple sources
        name = getattr(device, 'name', None)
        
        # Try Windows advertisement data
        if not name:
            details = getattr(device, 'details', None)
            if details and hasattr(details, 'Advertisement'):
                ad = details.Advertisement
                if hasattr(ad, 'LocalName'):
                    name = ad.LocalName
        
        # Try metadata
        if not name:
            metadata = getattr(device, 'metadata', {})
            if isinstance(metadata, dict):
                name = metadata.get('name', None) or metadata.get('local_name', None)
        
        return {
            'address': address,
            'name': name or 'Unknown Device',
            'last_seen': datetime.now().isoformat()
        }

    async def discover_devices(self, timeout_sec: float = 5.0) -> dict:
        """Discover RTMShunt devices only."""
        try:
            devices = await BleakScanner.discover(timeout=timeout_sec)
            device_list = []
            
            for device in devices:
                info = self._extract_device_info(device)
                ## Filter for RTMShunt devices only
                if info['name'].startswith('RTMShunt'):
                    device_list.append(info)
            
            if self.verbose:
                print(f"DEBUG: Discovered {len(device_list)} RTMShunt devices")
            
            # Load existing device list
            saved_devices = self.load_device_list()
            saved_addresses = {d['address'] for d in saved_devices}
            
            # Add newly discovered devices to saved list
            for device in device_list:
                if device['address'] not in saved_addresses:
                    saved_devices.append(device)
                else:
                    # Update last_seen for existing devices
                    for saved_device in saved_devices:
                        if saved_device['address'] == device['address']:
                            saved_device['last_seen'] = device['last_seen']
                            saved_device['name'] = device['name']
            
            # Save updated device list
            self.save_device_list(saved_devices)
            
            return {
                'success': True,
                'count': len(device_list),
                'devices': device_list,
                'saved_devices': saved_devices,
                'message': f'Found {len(device_list)} RTMShunt device(s)'
            }
        except Exception as exc:
            return {
                'success': False,
                'count': 0,
                'devices': [],
                'saved_devices': self.load_device_list(),
                'error': str(exc),
                'message': f'Discovery error: {str(exc)}'
            }

    async def add_device_manually(self, mac_address: str, name: str = None) -> dict:
        """Manually add a device to the device list."""
        try:
            normalized_mac = self._normalize_mac(mac_address)
            
            # Validate MAC format
            if len(normalized_mac.replace(':', '')) != 12:
                return {
                    'success': False,
                    'message': 'Invalid MAC address format. Expected: XX:XX:XX:XX:XX:XX'
                }
            
            saved_devices = self.load_device_list()
            
            # Check if device already exists
            existing_device = None
            for device in saved_devices:
                if self._normalize_mac(device['address']) == normalized_mac:
                    existing_device = device
                    break
            
            if existing_device:
                existing_device['last_seen'] = datetime.now().isoformat()
                if name:
                    existing_device['name'] = name
                message = f'Updated existing device: {existing_device["name"]}'
            else:
                new_device = {
                    'address': normalized_mac,
                    'name': name or f'RTMShunt (Manual)',
                    'last_seen': datetime.now().isoformat()
                }
                saved_devices.append(new_device)
                message = f'Added device: {new_device["name"]}'
            
            self.save_device_list(saved_devices)
            
            return {
                'success': True,
                'saved_devices': saved_devices,
                'message': message
            }
        except Exception as exc:
            return {
                'success': False,
                'message': f'Error adding device: {str(exc)}'
            }

    async def set_device(self, mac_address: str) -> dict:
        """Set the target device MAC address for connection."""
        try:
            normalized_mac = self._normalize_mac(mac_address)
            
            if len(normalized_mac.replace(':', '')) != 12:
                return {
                    'success': False,
                    'message': 'Invalid MAC address format'
                }
            
            # Find device name from saved list
            saved_devices = self.load_device_list()
            device_name = None
            for device in saved_devices:
                if self._normalize_mac(device['address']) == normalized_mac:
                    device_name = device['name']
                    break
            
            self.mac = normalized_mac
            with self.data_lock:
                self.latest_data['current_device_mac'] = normalized_mac
                self.latest_data['current_device_name'] = device_name
            
            return {
                'success': True,
                'mac': normalized_mac,
                'name': device_name,
                'message': f'Device set to: {device_name or normalized_mac}'
            }
        except Exception as exc:
            return {
                'success': False,
                'message': f'Error setting device: {str(exc)}'
            }
    
    async def connect_and_listen(self) -> None:
        """Connect to device and listen for notifications indefinitely."""
        if self.auto_connect:
            print(f"\n{'='*60}")
            print(f"Connecting to Shunt300: {self.mac}")
            print(f"{'='*60}\n")
        else:
            print(f"\n⏸️  Auto-connect disabled. Use 'Discover Devices' in UI to connect manually.\n")
        
        retry_count = 0

        while self.running:
            # Skip if manually disconnected or no MAC set
            if self.manual_disconnect or not self.mac or self.mac == '00:00:00:00:00:00':
                await asyncio.sleep(1.0)
                continue
            
            try:
                async with BleakClient(self.mac, timeout=20.0) as client:
                    self.client = client
                    
                    if not client.is_connected:
                        print("Connection failed")
                        retry_count += 1
                        await asyncio.sleep(min(20, 2 + retry_count * 2))
                        continue
                    
                    print("✅ Connected successfully!")
                    retry_count = 0
                    self.last_connect_time = time.time()
                    with self.data_lock:
                        self.latest_data['connected'] = True
                        self.latest_data['connection_status'] = 'connected'
                    
                    # Discover notify characteristics
                    services = client.services
                    notify_chars = []
                    for service in services:
                        for char in service.characteristics:
                            props = char.properties or []
                            if "notify" in props or "indicate" in props:
                                notify_chars.append(str(char.uuid))
                    
                    print(f"Notify characteristics found: {notify_chars}")
                    
                    # Try known UUID first, then fallback
                    subscribed_uuid = None
                    for uuid in [SHUNT_NOTIFY_UUID, FALLBACK_NOTIFY_UUID] + notify_chars:
                        try:
                            char = services.get_characteristic(uuid)
                            if char and ("notify" in char.properties or "indicate" in char.properties):
                                await client.start_notify(uuid, self.notification_handler)
                                subscribed_uuid = uuid
                                print(f"✅ Subscribed to: {uuid}")
                                break
                        except Exception:
                            continue
                    
                    if not subscribed_uuid:
                        print("❌ No notify characteristics available")
                        with self.data_lock:
                            self.latest_data['connection_status'] = 'no_notifications'
                        await asyncio.sleep(5)
                        continue

                    # Clear reconnect request once a new subscription is active.
                    # Otherwise a manual connect/reconnect request can immediately
                    # break this session before first notifications arrive.
                    self.reconnect_requested = False
                    self.reconnect_reason = None
                    
                    print(f"\n🔔 Listening for notifications... (Ctrl+C to stop)\n")
                    
                    # Keep connection alive
                    while self.running and client.is_connected:
                        if self.reconnect_requested or self.manual_disconnect:
                            break

                        if self.last_update_time is not None:
                            now = time.time()
                            age = now - self.last_update_time
                            connected_for = (now - self.last_connect_time) if self.last_connect_time else 0.0
                            cooldown_elapsed = (now - self.last_reconnect_attempt_time) >= self.stale_reconnect_cooldown_seconds
                            if (
                                age > self.stale_after_seconds
                                and connected_for >= self.min_connected_before_stale_check_seconds
                                and cooldown_elapsed
                            ):
                                print(f"⚠️ Stream stale for {int(age)}s. Triggering reconnect.")
                                await self.request_reconnect('stale_stream')
                                break

                        await asyncio.sleep(1)
                    
                    # Cleanup
                    if subscribed_uuid:
                        try:
                            await client.stop_notify(subscribed_uuid)
                        except:
                            pass
                    
                    print("\n📡 Disconnected from device")
                    
            except Exception as e:
                print(f"Connection error: {e}")
                retry_count += 1
                print(f"Retrying in {min(20, 2 + retry_count * 2)} seconds...")
                await asyncio.sleep(min(20, 2 + retry_count * 2))
        
        with self.data_lock:
            self.latest_data['connected'] = False
            self.latest_data['connection_status'] = 'disconnected'
            self.last_connect_time = None
    
    def get_live_data(self) -> dict:
        """Get latest sensor data for HTTP API."""
        with self.data_lock:
            if self.last_update_time:
                age_sec = time.time() - self.last_update_time
                self.latest_data['last_update_age_sec'] = round(age_sec, 1)
                self.latest_data['last_update_age_text'] = self.format_age(age_sec)

            now = time.time()
            elapsed = now - self.last_rate_calc_time
            if elapsed >= 1.0:
                current_count = self.latest_data['notification_count']
                delta_count = current_count - self.last_rate_calc_count
                self.packet_rate_per_sec = max(0.0, delta_count / elapsed)
                self.last_rate_calc_time = now
                self.last_rate_calc_count = current_count

            self.latest_data['packet_rate_per_sec'] = round(self.packet_rate_per_sec, 2)
            self.latest_data['reconnect_count'] = self.reconnect_count
            self.latest_data['last_reconnect_reason'] = self.last_reconnect_reason
            self.latest_data['last_reconnect_at'] = self.last_reconnect_at
            self.latest_data['stale_after_seconds'] = self.stale_after_seconds
            self.latest_data['stale_reconnect_cooldown_seconds'] = self.stale_reconnect_cooldown_seconds
            self.latest_data['configured_capacity_kwh'] = self.estimate_capacity_kwh

            if self.last_reconnect_attempt_time > 0:
                cooldown_remaining = self.stale_reconnect_cooldown_seconds - (now - self.last_reconnect_attempt_time)
                self.latest_data['reconnect_cooldown_remaining_sec'] = max(0, int(cooldown_remaining))
            else:
                self.latest_data['reconnect_cooldown_remaining_sec'] = 0

            if self.last_connect_time:
                connected_for = max(0.0, now - self.last_connect_time)
                self.latest_data['connected_for_sec'] = round(connected_for, 1)
                self.latest_data['connected_for_text'] = self.format_age(connected_for)
            else:
                self.latest_data['connected_for_sec'] = None
                self.latest_data['connected_for_text'] = 'n/a'
            
            # Add database info if available
            if self.db:
                self.latest_data['database_enabled'] = True
            else:
                self.latest_data['database_enabled'] = False
            
            return dict(self.latest_data)
    
    def run_ble_connection(self) -> None:
        """Run BLE connection in asyncio event loop."""
        self.running = True
        try:
            asyncio.run(self.connect_and_listen())
        except KeyboardInterrupt:
            print("\n⚠️  BLE connection interrupted")
        finally:
            self.running = False

    def open_dashboard_browser(self, host: str, port: int, delay_sec: float = 1.0) -> None:
        """Open the web dashboard in the default browser after startup."""
        try:
            if delay_sec > 0:
                time.sleep(delay_sec)
            browser_host = '127.0.0.1' if host in ('0.0.0.0', '::') else host
            dashboard_url = f"http://{browser_host}:{port}/"
            webbrowser.open(dashboard_url, new=1)
        except Exception as exc:
            if self.verbose:
                print(f"⚠️  Failed to open browser automatically: {exc}")

    def should_enable_tray(self) -> bool:
        return bool(self.enable_tray and os.name == 'nt' and getattr(sys, 'frozen', False))

    def load_tray_icon_image(self):
        if Image is None:
            return None
        icon_path = resolve_resource_path('installer_icon.ico')
        if icon_path.exists():
            try:
                return Image.open(icon_path)
            except Exception:
                pass
        return Image.new('RGB', (64, 64), (3, 169, 244))

    def request_shutdown(self) -> None:
        self.running = False
        server = self.http_server
        if server is not None:
            threading.Thread(target=server.shutdown, daemon=True).start()

    def start_tray_icon(self) -> None:
        if not self.should_enable_tray() or pystray is None:
            return
        tray_image = self.load_tray_icon_image()
        if tray_image is None:
            return

        def on_open(icon, item):
            self.open_dashboard_browser(self.host, self.port, delay_sec=0.0)

        def on_quit(icon, item):
            self.request_shutdown()
            icon.stop()

        tray_menu = pystray.Menu(
            pystray.MenuItem('Open Dashboard', on_open, default=True),
            pystray.MenuItem('Quit', on_quit)
        )
        self.tray_icon = pystray.Icon('renogy_shunt300_live_simulator', tray_image, 'Renogy Shunt300 Live Simulator', tray_menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def start(self, host: str = '127.0.0.1', port: int = 8081) -> None:
        """Start both BLE connection and HTTP server."""
        self.host = host
        self.port = port
        print(f"\n{'='*60}")
        print(f"RENOGY SHUNT300 LIVE SIMULATOR - RTMShunt Only")
        print(f"{'='*60}")
        print(f"Device MAC: {self.mac if self.mac != '00:00:00:00:00:00' else 'Not Set'}")
        print(f"Web Interface: http://{host}:{port}/")
        print(f"Live API: http://{host}:{port}/api/live")
        print(f"Battery Capacity: {self.estimate_capacity_kwh} kWh")
        print(f"{'='*60}\n")
        
        # Start BLE connection in background thread
        ble_thread = threading.Thread(target=self.run_ble_connection, daemon=True)
        ble_thread.start()
        
        # Start HTTP server in main thread
        simulator = self
        
        class SimulatorRequestHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(simulator.app_dir), **kwargs)
            
            def do_GET(self):
                parsed = urlparse(self.path)
                
                if parsed.path == '/api/live':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    data = simulator.get_live_data()
                    try:
                        self.wfile.write(json.dumps(data, indent=2).encode())
                    except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                        pass
                    return
                
                elif parsed.path == '/' or parsed.path == '/index.html':
                    html_path = resolve_resource_path('shunt300_live_ui.html')
                    if html_path.exists():
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                        self.send_header('Pragma', 'no-cache')
                        self.send_header('Expires', '0')
                        self.end_headers()
                        with open(html_path, 'rb') as f:
                            try:
                                self.wfile.write(f.read())
                            except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                                pass
                        return
                    else:
                        self.send_response(404)
                        self.end_headers()
                        error_msg = f"UI file not found at {html_path}".encode()
                        self.wfile.write(error_msg)
                        return
                
                # Serve static files (images, etc.) from resource directory
                elif parsed.path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico')):
                    static_path = resolve_resource_path(parsed.path.lstrip('/'))
                    if static_path.exists():
                        # Determine content type
                        content_types = {
                            '.png': 'image/png',
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg',
                            '.gif': 'image/gif',
                            '.webp': 'image/webp',
                            '.svg': 'image/svg+xml',
                            '.ico': 'image/x-icon'
                        }
                        ext = static_path.suffix.lower()
                        content_type = content_types.get(ext, 'application/octet-stream')
                        
                        self.send_response(200)
                        self.send_header('Content-type', content_type)
                        self.send_header('Cache-Control', 'public, max-age=86400')
                        self.end_headers()
                        with open(static_path, 'rb') as f:
                            try:
                                self.wfile.write(f.read())
                            except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                                pass
                        return
                    else:
                        self.send_response(404)
                        self.end_headers()
                        return
                
                super().do_GET()

            def do_POST(self):
                parsed = urlparse(self.path)
                if parsed.path != '/api/action':
                    self.send_response(404)
                    self.end_headers()
                    return

                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else b'{}'

                try:
                    payload = json.loads(body.decode('utf-8'))
                    action = payload.get('action', '').strip().lower()
                except Exception:
                    action = ''

                if action == 'connect':
                    asyncio.run(simulator.connect())
                    response = {'ok': True, 'action': 'connect', 'message': 'Connect requested'}
                elif action == 'disconnect':
                    asyncio.run(simulator.disconnect())
                    response = {'ok': True, 'action': 'disconnect', 'message': 'Disconnect requested'}
                elif action == 'force_disconnect':
                    asyncio.run(simulator.disconnect())
                    response = {'ok': True, 'action': 'force_disconnect', 'message': 'Force disconnect requested'}
                elif action == 'reconnect':
                    asyncio.run(simulator.request_reconnect('manual_ui'))
                    response = {'ok': True, 'action': 'reconnect', 'message': 'Reconnect requested'}
                elif action == 'reset_counters':
                    simulator.reset_counters()
                    response = {'ok': True, 'action': 'reset_counters', 'message': 'Counters reset'}
                elif action == 'set_capacity':
                    capacity_kwh = payload.get('capacity_kwh')
                    result = simulator.set_capacity(capacity_kwh)
                    response = {
                        'ok': result.get('success', False),
                        'action': 'set_capacity',
                        'message': result.get('message', 'Operation completed'),
                        'capacity_kwh': result.get('capacity_kwh'),
                        'estimated_energy_kwh': result.get('estimated_energy_kwh'),
                    }
                elif action == 'discover_devices':
                    discovery = asyncio.run(simulator.discover_devices())
                    response = {
                        'ok': discovery.get('success', False),
                        'action': 'discover_devices',
                        'message': discovery.get('message', 'Discovery completed'),
                        'discovery': discovery,
                    }
                elif action == 'add_device_manually':
                    mac = payload.get('mac_address', '')
                    name = payload.get('name', None)
                    result = asyncio.run(simulator.add_device_manually(mac, name))
                    response = {
                        'ok': result.get('success', False),
                        'action': 'add_device_manually',
                        'message': result.get('message', 'Operation completed'),
                        'saved_devices': result.get('saved_devices', []),
                    }
                elif action == 'set_device':
                    mac = payload.get('mac_address', '')
                    result = asyncio.run(simulator.set_device(mac))
                    response = {
                        'ok': result.get('success', False),
                        'action': 'set_device',
                        'message': result.get('message', 'Operation completed'),
                        'mac': result.get('mac'),
                        'name': result.get('name'),
                    }
                elif action == 'load_device_list':
                    saved_devices = simulator.load_device_list()
                    response = {
                        'ok': True,
                        'action': 'load_device_list',
                        'devices': saved_devices,
                        'message': f'Loaded {len(saved_devices)} saved devices'
                    }
                elif action == 'clear_device_list':
                    success = simulator.clear_device_list()
                    response = {
                        'ok': success,
                        'action': 'clear_device_list',
                        'message': 'Device list cleared' if success else 'Failed to clear device list'
                    }
                elif action == 'get_database_stats':
                    if simulator.db:
                        stats = simulator.db.get_database_stats()
                        response = {
                            'ok': True,
                            'action': 'get_database_stats',
                            'stats': stats,
                            'message': f'{stats["reading_count"]} readings logged'
                        }
                    else:
                        response = {'ok': False, 'message': 'Database not available'}
                elif action == 'get_sensor_history':
                    if simulator.db:
                        hours = payload.get('hours', 24)
                        limit = payload.get('limit', 100)
                        readings = simulator.db.get_sensor_readings(
                            device_address=simulator.mac if simulator.mac != '00:00:00:00:00:00' else None,
                            limit=limit
                        )
                        stats = simulator.db.get_reading_statistics(simulator.mac, hours) if simulator.mac != '00:00:00:00:00:00' else {}
                        response = {
                            'ok': True,
                            'action': 'get_sensor_history',
                            'readings': readings,
                            'statistics': stats,
                            'message': f'{len(readings)} readings retrieved'
                        }
                    else:
                        response = {'ok': False, 'message': 'Database not available'}
                elif action == 'clear_old_readings':
                    if simulator.db:
                        days = payload.get('days', 30)
                        deleted = simulator.db.clear_old_readings(days)
                        response = {
                            'ok': True,
                            'action': 'clear_old_readings',
                            'deleted_count': deleted,
                            'message': f'Deleted {deleted} old readings'
                        }
                    else:
                        response = {'ok': False, 'message': 'Database not available'}
                elif action == 'purge_database':
                    if simulator.db:
                        success = simulator.db.purge_all_data()
                        response = {
                            'ok': success,
                            'action': 'purge_database',
                            'message': 'Database purged successfully' if success else 'Failed to purge database'
                        }
                    else:
                        response = {'ok': False, 'message': 'Database not available'}
                elif action == 'restart_app':
                    response = {
                        'ok': True,
                        'action': 'restart_app',
                        'message': 'Restarting application...'
                    }
                    # Send response before restarting
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    try:
                        self.wfile.write(json.dumps(response).encode())
                    except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                        pass
                    # Restart the application
                    print("\n🔄 Restarting application...")
                    try:
                        if getattr(sys, 'frozen', False):
                            restart_cmd = [sys.executable] + sys.argv[1:]
                            restart_cwd = Path(sys.executable).resolve().parent
                        else:
                            restart_cmd = [sys.executable, Path(__file__).resolve()] + sys.argv[1:]
                            restart_cwd = Path(__file__).resolve().parent

                        kwargs = {
                            'cwd': str(restart_cwd),
                            'close_fds': True,
                        }
                        if os.name == 'nt':
                            kwargs['creationflags'] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

                        subprocess.Popen(restart_cmd, **kwargs)
                    except Exception as exc:
                        print(f"❌ Restart failed: {exc}")
                        return

                    def _delayed_exit() -> None:
                        time.sleep(0.6)
                        os._exit(0)

                    threading.Thread(target=_delayed_exit, daemon=True).start()
                    return
                else:
                    response = {'ok': False, 'message': 'Unknown action'}

                self.send_response(200 if response['ok'] else 400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                try:
                    self.wfile.write(json.dumps(response).encode())
                except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                    pass
            
            def log_message(self, format, *args):
                if simulator.verbose:
                    super().log_message(format, *args)
        
        try:
            server = HTTPServer((host, port), SimulatorRequestHandler)
            self.http_server = server
            print(f"✅ HTTP server started on http://{host}:{port}")
            print(f"🌐 Open browser to view live dashboard\n")
            self.start_tray_icon()
            if self.open_browser:
                threading.Thread(target=self.open_dashboard_browser, args=(host, port), daemon=True).start()
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n⚠️  Shutting down...")
        finally:
            self.running = False
            self.http_server = None
            if self.tray_icon:
                try:
                    self.tray_icon.stop()
                except Exception:
                    pass
                self.tray_icon = None
            if ble_thread.is_alive():
                ble_thread.join(timeout=2)


def main():
    parser = argparse.ArgumentParser(
        description='Renogy Shunt300 Live Simulator - RTMShunt BLE Monitor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start simulator (discover devices in UI)
  python shunt300_live_simulator_v2.py
  
  # Start with auto-connect to specific device
  python shunt300_live_simulator_v2.py 4C:E1:74:5C:94:8E --auto-connect
  
  # Custom port and battery capacity
  python shunt300_live_simulator_v2.py --port 8080 --capacity 2.56
  
  # Verbose mode
  python shunt300_live_simulator_v2.py --verbose
        """
    )
    
    parser.add_argument('mac', nargs='?', default='00:00:00:00:00:00',
                       help='BLE MAC address of RTMShunt (optional - use UI to discover)')
    parser.add_argument('--host', default='127.0.0.1', help='HTTP server host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8081, help='HTTP server port (default: 8081)')
    parser.add_argument('--capacity', type=float, default=0.0, 
                       help='Battery capacity in kWh (default: 0.0, set in UI)')
    parser.add_argument('--verbose', action='store_true', help='Show detailed logging')
    parser.add_argument('--auto-connect', action='store_true', 
                       help='Automatically connect to specified MAC on startup')
    parser.add_argument('--no-db-logging', action='store_true',
                       help='Disable SQLite database logging (experimental)')
    parser.add_argument('--no-browser', action='store_true',
                       help='Do not auto-open dashboard in default browser')
    parser.add_argument('--no-tray', action='store_true',
                       help='Disable Windows system tray icon')
    
    args = parser.parse_args()
    
    # Validate MAC if auto-connect requested
    if args.auto_connect and (not args.mac or args.mac == '00:00:00:00:00:00'):
        print("ERROR: --auto-connect requires a valid MAC address")
        sys.exit(1)
    
    if args.mac != '00:00:00:00:00:00' and len(args.mac.replace(':', '')) != 12:
        print("ERROR: Invalid MAC address format. Expected: XX:XX:XX:XX:XX:XX")
        sys.exit(1)
    
    simulator = Shunt300LiveSimulator(
        mac=args.mac,
        estimate_capacity_kwh=args.capacity,
        verbose=args.verbose,
        auto_connect=args.auto_connect,
        enable_db_logging=not args.no_db_logging,
        open_browser=not args.no_browser,
        enable_tray=not args.no_tray
    )
    
    try:
        simulator.start(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\n✅ Simulator stopped")


if __name__ == '__main__':
    main()

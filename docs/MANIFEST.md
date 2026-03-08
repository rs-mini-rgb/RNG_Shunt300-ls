# Shunt300 Standalone Simulator - Package Manifest

**Version:** 1.0.0  
**Date:** March 7, 2026  
**Platform:** Windows/macOS/Linux  

---

## Package Contents

```
Shunt300_Standalone_Simulator/
├── shunt300_live_simulator.py    (446 lines) - Main simulator application
├── shunt300_live_ui.html          (868 lines) - Web dashboard interface
├── README.md                      (550 lines) - Complete documentation
├── QUICKSTART.md                   (70 lines) - Quick start guide
├── requirements.txt                 (1 line) - Python dependencies (bleak)
├── LICENSE.txt                     (21 lines) - MIT License
├── config_examples.sh              (50 lines) - Configuration examples
└── MANIFEST.md                          (this file) - Package manifest
```

**Total:** 8 files, ~2,000 lines of code + documentation

---

## Features

✅ **Live BLE Connection** - Persistent connection to Shunt300  
✅ **Real-Time Streaming** - 21 sensors via notification mode  
✅ **Web Dashboard** - Modern UI with 2-second refresh  
✅ **Energy Estimation** - SOC-based calculation  
✅ **Status Detection** - Automatic charge/discharge/idle  
✅ **Auto-Reconnect** - Handles connection drops  
✅ **Cross-Platform** - Windows/macOS/Linux support  
✅ **Zero Dependencies** - Only requires `bleak` library  
✅ **Standalone** - No Home Assistant required  
✅ **No Log Files** - Direct device streaming  

---

## Requirements

### Hardware
- Renogy Shunt300 device
- Bluetooth adapter (built-in or USB)
- Computer within BLE range (~10m / 30ft)

### Software
- Python 3.8+ (tested on 3.10, 3.11, 3.12, 3.14)
- bleak 0.20.0+ (BLE library)

---

## Installation

```bash
# Install dependency
pip install -r requirements.txt

# Run simulator
python shunt300_live_simulator.py YOUR_MAC_ADDRESS

# Open browser
http://127.0.0.1:8765
```

---

## Sensor Coverage

### Primary Sensors (6)
- Voltage (V)
- Current (A)
- Power (W)
- SOC (%)
- Energy (kWh, estimated)
- Status (charging/discharging/idle)

### Diagnostic Sensors (3)
- Connection Status
- Notification Count
- Last Update Age

### Extended Sensors (12)
- Starter Voltage
- Temperature 1-3
- Historical Values 1-6
- Additional Value
- Sequence Number

**Total: 21 sensors**

---

## API Endpoints

### GET /
Serves web dashboard UI (HTML)

### GET /api/live
Returns JSON with all sensor data:
```json
{
  "voltage": 14.6,
  "current": 0.45,
  "power": 6.6,
  "soc": 100.0,
  "energy": null,
  "estimated_energy_kwh": 1.28,
  "status": "charging",
  "connection_status": "connected",
  "notification_count": 150,
  "last_update_age_sec": 2.1,
  "last_update_age_text": "2s",
  ...
}
```

---

## Testing

### Basic Test
```bash
python shunt300_live_simulator.py YOUR_MAC --verbose
# Wait for "✅ Connected successfully!"
# Open http://127.0.0.1:8765
# Verify "Record Age" shows "1-3s"
```

### API Test
```bash
curl http://127.0.0.1:8765/api/live
# Should return JSON with all sensors
```

### Connection Test
```bash
# Connect/disconnect charger or load
# Verify status changes in UI
# Watch notification count increase
```

---

## Deployment Scenarios

### 1. Local Monitoring
```bash
python shunt300_live_simulator.py YOUR_MAC
```
Access: http://127.0.0.1:8765 (same computer)

### 2. LAN Access
```bash
python shunt300_live_simulator.py YOUR_MAC --host 0.0.0.0
```
Access: http://YOUR_COMPUTER_IP:8765 (from any device on network)

### 3. Custom Port
```bash
python shunt300_live_simulator.py YOUR_MAC --port 8080
```
Access: http://127.0.0.1:8080

### 4. Multiple Devices
```bash
# Device 1
python shunt300_live_simulator.py MAC1 --port 8765

# Device 2 (different port)
python shunt300_live_simulator.py MAC2 --port 8766
```

---

## Known Limitations

1. **RSSI Unavailable** - `bleak` doesn't expose RSSI during connection
2. **Windows BLE Stall** - May drop after ~80 minutes (auto-reconnects)
3. **Single Connection** - One client per device (BLE limitation)
4. **No Logging** - Current version streams only (no file logging)
5. **Energy Estimation** - Estimated from SOC (direct field unavailable in notify mode)

---

## Troubleshooting

### Connection Failed
- ✅ Device powered with battery connected
- ✅ MAC address correct format (`XX:XX:XX:XX:XX:XX`)
- ✅ Within BLE range (~10m)
- ✅ No other BLE apps connected
- ✅ Bluetooth adapter enabled

### No Data Showing
- ⏱ Wait 5-10 seconds for first packet
- 🔍 Check console for connection status
- 🔄 Try power-cycling device

### Energy Incorrect
- 🔧 Set correct capacity: `--capacity X.XX`
- 📊 Default is 1.28 kWh (100Ah @ 12.8V)

---

## Distribution

### Sharing Package
1. **ZIP entire folder** (all 8 files)
2. Recipient installs Python + dependency
3. Recipient edits MAC address in command
4. Ready to run!

### Requirements
- Minimum: `shunt300_live_simulator.py` + `shunt300_live_ui.html`
- Recommended: Include README.md and requirements.txt
- Optional: QUICKSTART.md for ease of use

---

## Version History

### v1.0.0 (March 2026)
- Initial release
- Live BLE streaming
- 21 sensors supported
- Web dashboard
- Auto-reconnect
- Cross-platform

---

## License

MIT License - Free to use, modify, distribute

---

## Support

**Documentation:** README.md  
**Quick Start:** QUICKSTART.md  
**Configuration:** config_examples.sh  
**Issues:** See README.md Troubleshooting section  

---

**Package Ready for Distribution** ✅

Recipient needs:
1. Python 3.8+
2. `pip install bleak`
3. Their Shunt300 MAC address
4. Run: `python shunt300_live_simulator.py MAC`

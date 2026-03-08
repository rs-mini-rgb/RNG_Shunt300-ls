# Quick Start Guide

## Installation

1. **Install Python dependency:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Find your Shunt300 MAC address:**
   
   **Windows:**
   ```powershell
   Get-PnpDevice -Class Bluetooth | Where-Object {$_.FriendlyName -like "*Shunt*"}
   ```
   
   **macOS/Linux:**
   ```bash
   bluetoothctl
   scan on
   # Look for RNG-SHUNT device
   ```

3. **Run the simulator:**
   ```bash
   python shunt300_live_simulator.py YOUR_MAC_ADDRESS
   ```
   
   **Example:**
   ```bash
   python shunt300_live_simulator.py 4C:E1:74:5C:94:8E
   ```

4. **Open browser:**
   ```
   http://127.0.0.1:8081
   ```

## Options

```bash
# Custom battery capacity (2.56 kWh)
python shunt300_live_simulator.py YOUR_MAC --capacity 2.56

# Custom port
python shunt300_live_simulator.py YOUR_MAC --port 8080

# Verbose logging
python shunt300_live_simulator.py YOUR_MAC --verbose

# LAN access (from other devices)
python shunt300_live_simulator.py YOUR_MAC --host 0.0.0.0
```

## Troubleshooting

**Connection failed:**
- Check device is powered with battery connected
- Verify MAC address correct
- Move closer to device (BLE range ~10m)
- Disconnect other BLE apps

**No data showing:**
- Wait 5-10 seconds for first packet
- Check console for connection status
- Try power-cycling device

**Energy incorrect:**
- Set correct battery capacity: `--capacity X.XX`
- Default is 0.0 kWh (set in UI or via `--capacity`)

## Full Documentation

See [README.md](README.md) for complete documentation.

# v1.0.0 Release Notes

**Initial Release - RNG Shunt300 Live Simulator**

## Overview

RNG Shunt300 Live Simulator is a standalone web-based application for real-time monitoring of Renogy Shunt300 battery management devices via Bluetooth Low Energy (BLE).

## What's Included

- **Real-time BLE Connection**: Direct connection to Renogy Shunt300 (RTMShunt) devices
- **Modern Web Dashboard**: Clean, responsive UI for live data monitoring
- **Device Management**: Auto-discovery or manual MAC address entry
- **Telemetry Tracking**: Connection status, reconnection metrics, connection history
- **Data Persistence**: SQLite database for device list and historical data
- **Professional Installer**: Windows Inno Setup installer for easy deployment
- **Portable Option**: Self-contained ZIP for no-install scenarios

## System Requirements

- **OS**: Windows 10/11 (64-bit)
- **Bluetooth**: Built-in or USB Bluetooth adapter
- **Device**: Renogy Shunt300 (RTMShunt)
- **RAM**: 200MB minimum
- **Disk**: 50MB for installation

## Installation

### Option 1: Windows Installer (Recommended)

1. Download `Renogy_Shunt300LS_Setup.exe`
2. Run the installer
3. Follow the setup wizard
4. Launch from Start Menu or Desktop shortcut
5. Browser opens to `http://localhost:8089`

### Option 2: Portable (No Installation)

1. Download `Renogy_Shunt300LS_Portable.zip`
2. Extract to desired folder
3. Run `Shunt300LiveSimulator.exe`
4. Browser opens automatically to `http://localhost:8089`

### Verify Downloaded Files

All downloads should be hash-verified for integrity. Compare the SHA256 hash of your downloaded file with the values below.

**SHA256 Hashes:**
```
Renogy_Shunt300LS_Setup.exe
01BF0686785AE189548971093F284FE9403A25F4D6E556E212FADB94DA45D501

Renogy_Shunt300LS_Portable.zip
46C1F2E5D2FD90B0460F295ECA85921597DF63C25DD74129A27286D83D0E2FC0
```

**Verify on Windows (PowerShell):**

For Setup.exe:
```powershell
(Get-FileHash -Path "Renogy_Shunt300LS_Setup.exe" -Algorithm SHA256).Hash
```

For Portable.zip:
```powershell
(Get-FileHash -Path "Renogy_Shunt300LS_Portable.zip" -Algorithm SHA256).Hash
```

The output should match one of the hashes above. If it doesn't, the file may be corrupted or tampered with - do not run it.

## Getting Started

1. **Ensure Shunt300 is powered on** and within Bluetooth range
2. **Click "Connect"** on the dashboard
3. **Select your device** from the discovered list (or enter MAC address manually)
4. **Monitor real-time data** as it streams from the device

## Features

### Dashboard
- Live sensor readings (voltage, current, temperature, SOC, etc.)
- Connection status indicator
- Device information display
- Real-time charts and metrics

### Connection Management
- **Connect**: Fresh connection
- **Connected**: Active connection state
- **Reconnecting...**: Active reconnection in progress
- **Force Reconnect**: Manual reconnection trigger
- **Disconnect**: Graceful disconnect
- **Force Disconnect**: Immediate disconnect

### Telemetry
- Tracks reconnection count and reasons
- Shows connection uptime
- Reconnection cooldown monitoring
- Historical connection events

## Known Limitations

- **Windows Only**: Standalone build targets Windows 10/11 64-bit
- **No RSSI Display**: RSSI monitoring limited by Windows Bluetooth API
- **Single Device**: One concurrent device connection per instance
- **Local Network Only**: Dashboard accessible locally (port 8089)

## Network & Security

- **Local Only**: Dashboard runs on `http://localhost:8089`
- **No Cloud**: All data stays on your machine
- **No Sharing**: Not designed for multi-user network access
- **Firewall**: Windows may ask for firewall access on first run

## Troubleshooting

### Device Not Found
- Verify Shunt300 is powered on
- Check Bluetooth adapter is enabled
- Try manual MAC address entry
- Restart the application

### Connection Drops
- Check device battery level
- Look for Bluetooth interference (WiFi, microwave)
- Try Force Reconnect
- Check device is within range

### Port Already in Use
- Change port when launching: `Shunt300LiveSimulator.exe --port 8090`
- Close other applications using port 8089

## Building from Source

See [QUICKSTART.md](https://github.com/rs-mini-rgb/RNG_Shunt300-ls/blob/main/QUICKSTART.md) for build instructions.

Requirements:
- Python 3.10+
- PyInstaller + Inno Setup 6 (for building Windows installers)

## Code Signing

**v1.0.0 Note**: Executables are unsigned. They will show "Unknown developer" on first run. This is normal for new applications; Windows SmartScreen learns they're legitimate after repeated safe usage.

Future releases will include official code signing once the application builds reputation and usage.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](https://github.com/rs-mini-rgb/RNG_Shunt300-ls/blob/main/CONTRIBUTING.md) for guidelines.

## License

MIT License - See [LICENSE.txt](https://github.com/rs-mini-rgb/RNG_Shunt300-ls/blob/main/LICENSE.txt)

## Support

- **Issues**: https://github.com/rs-mini-rgb/RNG_Shunt300-ls/issues
- **Discussions**: https://github.com/rs-mini-rgb/RNG_Shunt300-ls/discussions
- **Documentation**: https://github.com/rs-mini-rgb/RNG_Shunt300-ls/blob/main/README.md

## Changelog

### v1.0.0 (Initial Release)
- ✅ Live BLE connection to Shunt300
- ✅ Real-time web dashboard
- ✅ Device discovery and management
- ✅ Connection telemetry tracking
- ✅ Windows installer
- ✅ Portable standalone distribution

---

**Thank you for using RNG Shunt300 Live Simulator!**

*Renogy Shunt300 is a registered trademark of Renogy. This is a community-developed monitoring application.*

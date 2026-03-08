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
5. Browser opens to `http://localhost:8081`

### Option 2: Portable (No Installation)

1. Download `Renogy_Shunt300LS_Portable.zip`
2. Extract to desired folder
3. Run `Shunt300LiveSimulator.exe`
4. Browser opens automatically to `http://localhost:8081`

### Verify Downloaded Files

All downloads should be hash-verified for integrity. Compare the SHA256 hash of your downloaded file with the values below.

**SHA256 Hashes:**
```
Renogy_Shunt300LS_Setup.exe
3983151A8AFA6D6A2113120FFD1CF0DFF15B0CD6A2BBD933F36C2485EEFD5940

Renogy_Shunt300LS_Portable.zip
6A86B98A5C9C4FDBC6CFF8FE8C5250CA37FF3131A7F2FBB4609E28736DF793B0
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

## Windows SmartScreen / Security Warning

### Expected Behavior on First Run

When you download and run the installer or portable executable, **Windows will likely show a security warning**:

- **"Windows protected your PC"**
- **"Microsoft Defender SmartScreen prevented an unrecognized app from starting"**
- **Publisher: Unknown publisher**

**This is normal and expected for new applications.**

### Why This Happens

This warning is triggered by two factors:

1. **Mark of the Web (MOTW)**: Windows tags files downloaded from the internet with a "Zone Identifier" that marks them as potentially untrusted.
2. **No Digital Signature**: v1.0.0 does not include a code-signing certificate. Digital signatures require purchasing a certificate from a Certificate Authority (CA), which will be considered for future releases once the application builds reputation and community trust.

### Is This Safe?

**Yes**, if you downloaded from the official release page: `https://github.com/rs-mini-rgb/RNG_Shunt300-ls/releases`

- **Verify the SHA256 hash** (see above) to ensure file integrity
- **Review the source code** on GitHub - this is open source
- **Check the publisher**: rs-mini-rgb Community (on GitHub)

### How to Run the Application

**Option 1: Click "More info" → "Run anyway"** (Recommended for most users)

1. When SmartScreen appears, click **"More info"**
2. Click **"Run anyway"** at the bottom
3. The application will launch normally

**Option 2: Unblock the file before running** (Alternative method)

1. Right-click the downloaded `.exe` or `.zip` file
2. Select **Properties**
3. At the bottom of the **General** tab, look for **"Security"** section
4. Check the box: **"Unblock"** (or click **"Unblock"** button)
5. Click **"Apply"** → **"OK"**
6. Run the file normally

**Note**: After you unblock and run the application once, Windows SmartScreen builds trust. Subsequent runs won't show the warning.

### Future Plans

We plan to add a digital code-signing certificate in future releases once:
- The application gains community usage and reputation
- Funds are available for purchasing a certificate from a trusted CA (Certificate Authority)
- The project demonstrates long-term sustainability

Until then, the SHA256 hash verification and open-source transparency provide security assurance.

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
- **Local Network Only**: Dashboard accessible locally (port 8081)

## Network & Security

- **Local Only**: Dashboard runs on `http://localhost:8081`
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

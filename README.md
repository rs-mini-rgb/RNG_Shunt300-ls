# RNG Shunt300 Live Simulator

A standalone web-based simulator and live data monitor for the Renogy Shunt300 (RTMShunt) BLE device.

## Features

- **Live BLE Connection**: Connects directly to Shunt300 devices via Bluetooth Low Energy
- **Web Dashboard**: Real-time monitoring interface accessible from any browser
- **Device Discovery**: Auto-discover nearby Shunt300 devices or manually enter MAC addresses
- **Data Persistence**: SQLite database stores device list and historical data
- **Telemetry Tracking**: Monitor connection status, reconnect counts, and connection history
- **Windows Standalone**: Self-contained executable with no external dependencies required
- **Installer Package**: Professional Inno Setup installer for easy distribution

## Quick Start

### Running from Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rs-mini-rgb/RNG_Shunt300-ls.git
   cd RNG_Shunt300-ls
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the simulator:**
   ```bash
   python src/shunt300_live_simulator.py
   ```

4. **Open in browser:**
   Navigate to `http://localhost:8081` (default port)

### Using Pre-Built Executable

Download the latest `Renogy_Shunt300LS_Setup.exe` from [releases](https://github.com/rs-mini-rgb/RNG_Shunt300-ls/releases) and run the installer.

**⚠️ Windows SmartScreen Warning**: You may see "Windows protected your PC" when running the installer. This is normal for new applications without code signing certificates. Click **"More info"** → **"Run anyway"** to proceed. See [RELEASE_NOTES_v1.0.0.md](RELEASE_NOTES_v1.0.0.md#windows-smartscreen--security-warning) for detailed security information.

**Code signing policy**: See [docs/CODE_SIGNING_POLICY.md](docs/CODE_SIGNING_POLICY.md).

**Signed release pipeline**: GitHub Actions workflow [release-build-sign.yml](.github/workflows/release-build-sign.yml) builds and signs release artifacts through SignPath once onboarding secrets are configured.

## Project Structure

```
RNG_Shunt300-ls/
├── src/                          # Source code
│   ├── shunt300_live_simulator.py # Main application
│   ├── shunt300_live_ui.html      # Web interface
│   └── shunt300_database.py       # Database layer
├── build/                         # Build configuration
│   ├── Shunt300LiveSimulator.spec # PyInstaller spec
│   ├── Shunt300LiveSimulator_Setup.iss # Inno Setup config
│   ├── build_windows_exe.ps1      # EXE build script
│   └── build_installer.ps1        # Installer build script
├── resources/                     # Images & branding
│   ├── installer_logo_banner.bmp
│   ├── installer_logo_small.bmp
│   ├── installer_icon.ico
│   └── RSHST-B02P300.webp
├── docs/                          # Documentation
│   └── MANIFEST.md
├── requirements.txt               # Python dependencies
├── LICENSE.txt                    # MIT License
├── README.md                      # This file
└── QUICKSTART.md                  # Quick start guide
```

## System Requirements

- **Windows 10/11** (64-bit) for executable builds
- **Python 3.10+** (for source builds)
- **Bluetooth adapter** (for BLE connectivity)
- **Renogy Shunt300 (RTMShunt)** device

## Building from Source

### Windows Executable

Requires: Python 3.10+, PyInstaller, Inno Setup 6

```powershell
cd build
.\build_windows_exe.ps1          # Creates dist/Shunt300LiveSimulator/
.\build_installer.ps1             # Creates Renogy_Shunt300LS_Setup.exe
```

## API Endpoints

- `GET /api/live` - Retrieve current device status & telemetry
- `POST /api/action` - Execute device actions (connect, reconnect, disconnect)

## Configuration

### Command-Line Options

```bash
python src/shunt300_live_simulator.py --port 8090
```

### Device Actions

From the web dashboard:
- **Connect**: Fresh connection without counting as reconnect
- **Connected**: Current connection state (displays when connected)
- **Reconnecting...**: Active reconnection in progress
- **Force Reconnect**: Trigger reconnection attempt
- **Disconnect**: Graceful disconnect
- **Force Disconnect**: Immediate disconnect

## Telemetry

The simulator tracks and displays:

- **Connection Status**: Current connection state
- **Reconnect Count**: Total manual reconnection attempts
- **Last Reconnect Reason**: Why the last reconnect occurred
- **Connected Duration**: How long the current connection has been active
- **Reconnect Cooldown**: Remaining time before next reconnect is allowed

## Troubleshooting

### Device Not Found

- Ensure device is powered on and in range
- Check Bluetooth adapter is enabled
- Try manual MAC address entry if auto-discovery fails

### Connection Drops

- Verify device has sufficient battery
- Check for Bluetooth interference
- Try reconnecting device manually

### Port Already in Use

Specify alternate port: `python src/shunt300_live_simulator.py --port 8090`

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License—see [LICENSE.txt](LICENSE.txt) for details.

## Support

For issues, questions, or feature requests, please open an [issue](https://github.com/rs-mini-rgb/RNG_Shunt300-ls/issues) on GitHub.

---

**Renogy Shunt300** is a registered trademark of Renogy. This project is a community-developed simulator and monitoring tool.

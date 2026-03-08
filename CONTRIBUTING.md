# Contributing Guide

Thank you for your interest in contributing to RNG Shunt300 Live Simulator! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Windows 10/11 (64-bit) for building executables

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/RNG_Shunt300-ls.git
   cd RNG_Shunt300-ls
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify setup:**
   ```bash
   python src/shunt300_live_simulator.py
   # Navigate to http://localhost:8081
   ```

## Development Workflow

### Code Style

- Follow PEP 8 conventions for Python
- Use descriptive variable and function names
- Add docstrings to functions and classes
- Keep lines under 100 characters where practical

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or for bug fixes:
   git checkout -b bugfix/issue-description
   ```

2. **Make your changes:**
   - Edit files in `src/` for Python code
   - Edit `src/shunt300_live_ui.html` for UI changes
   - Update `requirements.txt` if adding dependencies

3. **Test your changes:**
   ```bash
   python src/shunt300_live_simulator.py
   # Test in browser at http://localhost:8081
   ```

4. **Commit with clear messages:**
   ```bash
   git commit -m "Add feature: description of what was added"
   ```

### Pull Request Process

1. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a Pull Request:**
   - Provide a clear title and description
   - Reference any related issues
   - Include testing notes

3. **Wait for review:**
   - Address feedback promptly
   - Keep commits clean and logical

## Building for Distribution

### Windows Executable

To build a Windows EXE and installer:

```powershell
cd build
.\build_windows_exe.ps1    # Builds exe in dist/
.\build_installer.ps1      # Creates setup .exe in installer_output/
```

**Requirements:**
- PyInstaller: `pip install pyinstaller`
- Inno Setup 6: Download from https://jrsoftware.org/isdl.php

### Build Artifacts

**Do not commit:**
- `dist/` - PyInstaller output
- `build/` - Temporary build files
- `*.exe` - Compiled installers
- `__pycache__/` - Python cache

These are handled by `.gitignore`.

## Project Structure

```
src/
  ├── shunt300_live_simulator.py  # Main application, HTTP server, BLE logic
  ├── shunt300_live_ui.html       # Web interface (HTML/CSS/JavaScript)
  └── shunt300_database.py        # SQLite database handling

build/
  ├── Shunt300LiveSimulator.spec  # PyInstaller configuration
  ├── Shunt300LiveSimulator_Setup.iss  # Inno Setup configuration
  ├── build_windows_exe.ps1       # Build script
  └── build_installer.ps1         # Installer creation script

resources/
  └── [Images and branding assets]

docs/
  └── [Additional documentation]
```

## Code Areas

### BLE Connection (`shunt300_live_simulator.py`)
- Device discovery and connection logic
- Notification handling
- Sensor data parsing
- Connection state management

### Web Interface (`shunt300_live_ui.html`)
- Real-time data display
- User controls (connect, disconnect, etc.)
- Status indicators
- Data polling and error handling

### Database (`shunt300_database.py`)
- Device list persistence
- Recording storage
- Data export/import

## Issue Types

### Bug Reports
- Describe the issue clearly
- Include steps to reproduce
- Note your OS and Python version
- Attach relevant logs if applicable

### Feature Requests
- Explain the use case
- Describe desired behavior
- Note any UI/UX considerations

### Documentation
- Identify unclear sections
- Suggest improvements
- Add examples if helpful

## Questions?

- Check existing issues: https://github.com/rs-mini-rgb/RNG_Shunt300-ls/issues
- Feel free to ask in discussions or open an issue for clarification

## License

By contributing, you agree that your contributions will be licensed under the same MIT License that covers the project.

---

Thank you for helping make RNG Shunt300 LS better!

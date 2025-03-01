# OBD-II Diagnostic Application

A Python desktop application for interacting with an ELM327 WiFi adapter to monitor and diagnose vehicles, specifically designed for Fiat 500 Series 1, Toyota C-HR/Corolla, and Volkswagen Group vehicles.

## Features

### Connection
- WiFi connection to ELM327 adapter (IP: 192.168.0.10, port: 35000)
- Support for multiple OBD-II protocols with auto-detection
- Vehicle-specific protocol selection

### Dashboard
- Real-time display of vehicle metrics:
  - Speed (km/h)
  - RPM
  - Engine temperature (°C)
  - Fuel level (%)
  - Intake pressure (kPa)
- Vehicle-specific metrics for Fiat, Toyota, and VAG
- Dynamic graphs with 30-second history

### Diagnostics
- Read Diagnostic Trouble Codes (DTCs)
- Display code descriptions
- Clear DTCs
- Export data to CSV

## Requirements

- Python 3.9+
- PyQt5
- PyQtGraph
- Socket (built-in)

## Installation

1. Make sure you have Python 3.9 or newer installed
2. Install required packages:

```bash
pip install pyqt5 pyqtgraph
```

3. Run the application:

```bash
python obd_diagnostic_app.py
```

## Usage

1. Connect your computer to the ELM327 WiFi network
2. Select your vehicle type from the dropdown
3. Click "Connect" to establish connection
4. View real-time data on the Dashboard tab
5. Use the Diagnostics tab to read and clear DTCs
6. Export data using the "Export Data" button

## Vehicle Support

- **Fiat 500 Series 1**: KWP2000 protocol with ISO 9141-2 fallback
- **Toyota C-HR/Corolla**: CAN 11-bit 500kbps
- **Volkswagen Group**: CAN with KWP1281 fallback

## Notes

- The application is optimized for Windows with NVIDIA GPU acceleration
- PyQtGraph is used for high-performance graphics rendering
- Custom vehicle-specific PIDs can be added in the code
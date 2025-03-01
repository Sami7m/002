import sys
import socket
import time
import csv
from datetime import datetime
from collections import deque
import threading
import re

# PyQt5 for UI
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QTabWidget, 
                            QGridLayout, QMessageBox, QFileDialog, QComboBox,
                            QFrame, QSplitter, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QPalette

# PyQtGraph for performance with GPU acceleration
import pyqtgraph as pg

# Constants
DEFAULT_IP = "192.168.0.10"
DEFAULT_PORT = 35000
BUFFER_SIZE = 1024
TIMEOUT = 2  # seconds
UPDATE_INTERVAL = 1000  # milliseconds
GRAPH_HISTORY = 30  # seconds of data to show

# OBD-II PIDs (Standard)
PID_SPEED = "010D"
PID_RPM = "010C"
PID_ENGINE_TEMP = "0105"
PID_FUEL_LEVEL = "012F"
PID_INTAKE_PRESSURE = "010B"

# Vehicle-specific PIDs (hypothetical, to be customized)
# Fiat 500 specific
PID_FIAT_TURBO_PRESSURE = "015F"
PID_FIAT_CLUTCH_STATUS = "0160"

# Toyota specific
PID_TOYOTA_FUEL_CONSUMPTION = "015E"
PID_TOYOTA_HYBRID_BATTERY = "01A2"

# VAG specific
PID_VAG_BOOST_PRESSURE = "01A6"
PID_VAG_OIL_TEMP = "015C"

# OBD-II Commands
CMD_RESET = "ATZ"
CMD_VERSION = "ATI"
CMD_ECHO_OFF = "ATE0"
CMD_HEADERS_OFF = "ATH0"
CMD_LINEFEEDS_OFF = "ATL0"
CMD_AUTO_PROTOCOL = "ATSP0"
CMD_KWP2000 = "ATSP4"
CMD_ISO9141 = "ATSP3"
CMD_CAN_11BIT_500K = "ATSP6"
CMD_KWP1281 = "ATSP5"
CMD_READ_DTC = "03"
CMD_CLEAR_DTC = "04"

# DTC Codes Dictionary (sample)
DTC_CODES = {
    "P0100": "Mass or Volume Air Flow Circuit Malfunction",
    "P0101": "Mass or Volume Air Flow Circuit Range/Performance Problem",
    "P0102": "Mass or Volume Air Flow Circuit Low Input",
    "P0103": "Mass or Volume Air Flow Circuit High Input",
    "P0104": "Mass or Volume Air Flow Circuit Intermittent",
    "P0105": "Manifold Absolute Pressure/Barometric Pressure Circuit Malfunction",
    "P0106": "Manifold Absolute Pressure/Barometric Pressure Circuit Range/Performance Problem",
    "P0107": "Manifold Absolute Pressure/Barometric Pressure Circuit Low Input",
    "P0108": "Manifold Absolute Pressure/Barometric Pressure Circuit High Input",
    "P0109": "Manifold Absolute Pressure/Barometric Pressure Circuit Intermittent",
    "P0110": "Intake Air Temperature Circuit Malfunction",
    "P0111": "Intake Air Temperature Circuit Range/Performance Problem",
    "P0112": "Intake Air Temperature Circuit Low Input",
    "P0113": "Intake Air Temperature Circuit High Input",
    "P0114": "Intake Air Temperature Circuit Intermittent",
    "P0115": "Engine Coolant Temperature Circuit Malfunction",
    "P0116": "Engine Coolant Temperature Circuit Range/Performance Problem",
    "P0117": "Engine Coolant Temperature Circuit Low Input",
    "P0118": "Engine Coolant Temperature Circuit High Input",
    "P0119": "Engine Coolant Temperature Circuit Intermittent",
    "P0120": "Throttle Position Sensor/Switch A Circuit Malfunction",
    "P0121": "Throttle Position Sensor/Switch A Circuit Range/Performance Problem",
    "P0122": "Throttle Position Sensor/Switch A Circuit Low Input",
    "P0123": "Throttle Position Sensor/Switch A Circuit High Input",
    "P0124": "Throttle Position Sensor/Switch A Circuit Intermittent",
    "P0125": "Insufficient Coolant Temperature for Closed Loop Fuel Control",
    "P0126": "Insufficient Coolant Temperature for Stable Operation",
    "P0128": "Coolant Thermostat (Coolant Temperature Below Thermostat Regulating Temperature)",
    "P0130": "O2 Sensor Circuit Malfunction (Bank 1 Sensor 1)",
    "P0131": "O2 Sensor Circuit Low Voltage (Bank 1 Sensor 1)",
    "P0132": "O2 Sensor Circuit High Voltage (Bank 1 Sensor 1)",
    "P0133": "O2 Sensor Circuit Slow Response (Bank 1 Sensor 1)",
    "P0134": "O2 Sensor Circuit No Activity Detected (Bank 1 Sensor 1)",
    "P0135": "O2 Sensor Heater Circuit Malfunction (Bank 1 Sensor 1)",
    "P0171": "System Too Lean (Bank 1)",
    "P0172": "System Too Rich (Bank 1)",
    "P0300": "Random/Multiple Cylinder Misfire Detected",
    "P0301": "Cylinder 1 Misfire Detected",
    "P0302": "Cylinder 2 Misfire Detected",
    "P0303": "Cylinder 3 Misfire Detected",
    "P0304": "Cylinder 4 Misfire Detected",
    # Add more codes as needed
}

# Vehicle profiles
VEHICLE_PROFILES = {
    "Fiat 500 Series 1": {
        "protocol_cmd": CMD_KWP2000,
        "fallback_cmd": CMD_ISO9141,
        "specific_pids": {
            "Turbo Pressure": PID_FIAT_TURBO_PRESSURE,
            "Clutch Status": PID_FIAT_CLUTCH_STATUS
        }
    },
    "Toyota C-HR/Corolla": {
        "protocol_cmd": CMD_CAN_11BIT_500K,
        "fallback_cmd": CMD_AUTO_PROTOCOL,
        "specific_pids": {
            "Fuel Consumption": PID_TOYOTA_FUEL_CONSUMPTION,
            "Hybrid Battery": PID_TOYOTA_HYBRID_BATTERY
        }
    },
    "Volkswagen Group": {
        "protocol_cmd": CMD_CAN_11BIT_500K,
        "fallback_cmd": CMD_KWP1281,
        "specific_pids": {
            "Boost Pressure": PID_VAG_BOOST_PRESSURE,
            "Oil Temperature": PID_VAG_OIL_TEMP
        }
    }
}

# Theme colors
COLORS = {
    "background": "#2C2F33",
    "text": "#FFFFFF",
    "accent": "#7289DA",
    "accent_hover": "#5B6EBF",
    "success": "#43B581",
    "error": "#FF5555",
    "warning": "#FAA61A",
    "graph_line": "#7289DA",
    "graph_background": "#2C2F33",
    "grid_line": "#3E4147"
}

class OBDConnection(QThread):
    """Thread for handling OBD-II connection and communication"""
    connected = pyqtSignal(bool, str)
    data_received = pyqtSignal(dict)
    dtc_received = pyqtSignal(list)
    
    def __init__(self, ip=DEFAULT_IP, port=DEFAULT_PORT):
        super().__init__()
        self.ip = ip
        self.port = port
        self.socket = None
        self.is_connected = False
        self.running = False
        self.vehicle_profile = None
        self.protocol_detected = None
        
    def connect_obd(self):
        """Establish connection to the ELM327 device"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(TIMEOUT)
            self.socket.connect((self.ip, self.port))
            
            # Initialize ELM327
            responses = []
            
            # Reset device
            response = self.send_command(CMD_RESET)
            responses.append(f"Reset: {response}")
            
            # Get version
            response = self.send_command(CMD_VERSION)
            responses.append(f"Version: {response}")
            
            # Turn echo off
            self.send_command(CMD_ECHO_OFF)
            
            # Turn headers off
            self.send_command(CMD_HEADERS_OFF)
            
            # Turn linefeeds off
            self.send_command(CMD_LINEFEEDS_OFF)
            
            # Set protocol based on vehicle profile
            if self.vehicle_profile:
                protocol_cmd = VEHICLE_PROFILES[self.vehicle_profile]["protocol_cmd"]
                response = self.send_command(protocol_cmd)
                
                if "OK" not in response:
                    # Try fallback protocol
                    fallback_cmd = VEHICLE_PROFILES[self.vehicle_profile]["fallback_cmd"]
                    response = self.send_command(fallback_cmd)
                    
                self.protocol_detected = self.send_command("ATDP")
                responses.append(f"Protocol: {self.protocol_detected}")
            else:
                # Auto detect protocol
                response = self.send_command(CMD_AUTO_PROTOCOL)
                self.protocol_detected = self.send_command("ATDP")
                responses.append(f"Protocol: {self.protocol_detected}")
            
            self.is_connected = True
            self.connected.emit(True, "\n".join(responses))
            return True
            
        except Exception as e:
            self.is_connected = False
            self.connected.emit(False, f"Connection error: {str(e)}")
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    def disconnect_obd(self):
        """Disconnect from the ELM327 device"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.is_connected = False
        
    def send_command(self, command):
        """Send a command to the ELM327 device and return the response"""
        if not self.socket:
            return "Not connected"
            
        try:
            # Add carriage return to the command
            command = command + "\r"
            self.socket.send(command.encode())
            
            # Read the response
            response = b""
            start_time = time.time()
            
            while b'>' not in response and (time.time() - start_time) < TIMEOUT:
                chunk = self.socket.recv(BUFFER_SIZE)
                if not chunk:
                    break
                response += chunk
                
            # Decode and clean the response
            decoded = response.decode('utf-8', errors='replace').strip()
            decoded = decoded.replace("\r", "").replace("\n", " ").replace(">", "").strip()
            
            # Remove echo if present
            if decoded.startswith(command.strip()):
                decoded = decoded[len(command.strip()):].strip()
                
            return decoded
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def parse_pid_response(self, response, pid):
        """Parse the response for a specific PID"""
        if "NO DATA" in response or "ERROR" in response or not response:
            return None
            
        # Remove spaces and unwanted characters
        response = response.replace(" ", "")
        
        # Check if the response contains the PID
        if pid[2:4].lower() in response.lower():
            # Extract data bytes (depends on the PID)
            if pid == PID_SPEED:  # Speed
                if len(response) >= 4:
                    try:
                        # A single byte for km/h
                        data_byte = int(response[-2:], 16)
                        return data_byte  # km/h
                    except:
                        return None
                        
            elif pid == PID_RPM:  # RPM
                if len(response) >= 6:
                    try:
                        # Two bytes for RPM: (256*A + B) / 4
                        a = int(response[-4:-2], 16)
                        b = int(response[-2:], 16)
                        return (256 * a + b) / 4  # RPM
                    except:
                        return None
                        
            elif pid == PID_ENGINE_TEMP:  # Engine temperature
                if len(response) >= 4:
                    try:
                        # A single byte: A - 40 (Celsius)
                        data_byte = int(response[-2:], 16)
                        return data_byte - 40  # Celsius
                    except:
                        return None
                        
            elif pid == PID_FUEL_LEVEL:  # Fuel level
                if len(response) >= 4:
                    try:
                        # A single byte: A * 100 / 255 (percentage)
                        data_byte = int(response[-2:], 16)
                        return data_byte * 100 / 255  # Percentage
                    except:
                        return None
                        
            elif pid == PID_INTAKE_PRESSURE:  # Intake pressure
                if len(response) >= 4:
                    try:
                        # A single byte: A (kPa)
                        data_byte = int(response[-2:], 16)
                        return data_byte  # kPa
                    except:
                        return None
                        
            # Vehicle-specific PIDs (hypothetical parsing, to be customized)
            elif pid in [PID_FIAT_TURBO_PRESSURE, PID_VAG_BOOST_PRESSURE]:
                if len(response) >= 4:
                    try:
                        # Hypothetical: A * 2 (kPa)
                        data_byte = int(response[-2:], 16)
                        return data_byte * 2  # kPa
                    except:
                        return None
                        
            elif pid == PID_FIAT_CLUTCH_STATUS:
                if len(response) >= 4:
                    try:
                        # Hypothetical: 0 = disengaged, 1 = engaged
                        data_byte = int(response[-2:], 16)
                        return data_byte  # 0 or 1
                    except:
                        return None
                        
            elif pid == PID_TOYOTA_FUEL_CONSUMPTION:
                if len(response) >= 4:
                    try:
                        # Hypothetical: A / 10 (L/100km)
                        data_byte = int(response[-2:], 16)
                        return data_byte / 10  # L/100km
                    except:
                        return None
                        
            elif pid == PID_TOYOTA_HYBRID_BATTERY:
                if len(response) >= 4:
                    try:
                        # Hypothetical: A * 100 / 255 (percentage)
                        data_byte = int(response[-2:], 16)
                        return data_byte * 100 / 255  # Percentage
                    except:
                        return None
                        
            elif pid == PID_VAG_OIL_TEMP:
                if len(response) >= 4:
                    try:
                        # Hypothetical: A - 40 (Celsius)
                        data_byte = int(response[-2:], 16)
                        return data_byte - 40  # Celsius
                    except:
                        return None
        
        return None
    
    def read_dtc(self):
        """Read Diagnostic Trouble Codes"""
        if not self.is_connected or not self.socket:
            return []
            
        response = self.send_command(CMD_READ_DTC)
        dtc_codes = []
        
        if "NO DATA" not in response and "ERROR" not in response and response:
            # Parse DTC codes from the response
            # Format depends on protocol, but typically:
            # Each code is 2 bytes: first nibble is the code type, remaining 3 nibbles are the code number
            response = response.replace(" ", "")
            
            # Extract pairs of bytes
            i = 0
            while i < len(response) - 3:
                try:
                    code_bytes = response[i:i+4]
                    if code_bytes != "0000":  # Skip empty codes
                        first_char = ""
                        if code_bytes[0] == '0':
                            first_char = "P"  # Powertrain
                        elif code_bytes[0] == '1':
                            first_char = "C"  # Chassis
                        elif code_bytes[0] == '2':
                            first_char = "B"  # Body
                        elif code_bytes[0] == '3':
                            first_char = "U"  # Network
                            
                        code_number = code_bytes[1:4]
                        full_code = first_char + code_number
                        
                        # Get description if available
                        description = DTC_CODES.get(full_code, "Unknown code")
                        dtc_codes.append((full_code, description))
                except:
                    pass
                i += 4
        
        self.dtc_received.emit(dtc_codes)
        return dtc_codes
    
    def clear_dtc(self):
        """Clear Diagnostic Trouble Codes"""
        if not self.is_connected or not self.socket:
            return False
            
        response = self.send_command(CMD_CLEAR_DTC)
        return "OK" in response
    
    def run(self):
        """Main thread loop for continuous data polling"""
        self.running = True
        
        while self.running and self.is_connected:
            try:
                data = {}
                
                # Read standard PIDs
                response = self.send_command(PID_SPEED)
                data["speed"] = self.parse_pid_response(response, PID_SPEED)
                
                response = self.send_command(PID_RPM)
                data["rpm"] = self.parse_pid_response(response, PID_RPM)
                
                response = self.send_command(PID_ENGINE_TEMP)
                data["engine_temp"] = self.parse_pid_response(response, PID_ENGINE_TEMP)
                
                response = self.send_command(PID_FUEL_LEVEL)
                data["fuel_level"] = self.parse_pid_response(response, PID_FUEL_LEVEL)
                
                response = self.send_command(PID_INTAKE_PRESSURE)
                data["intake_pressure"] = self.parse_pid_response(response, PID_INTAKE_PRESSURE)
                
                # Read vehicle-specific PIDs if a profile is selected
                if self.vehicle_profile:
                    specific_pids = VEHICLE_PROFILES[self.vehicle_profile]["specific_pids"]
                    
                    for name, pid in specific_pids.items():
                        response = self.send_command(pid)
                        data[name.lower().replace(" ", "_")] = self.parse_pid_response(response, pid)
                
                # Emit the data
                self.data_received.emit(data)
                
                # Sleep to avoid flooding the ELM327
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error in data polling: {str(e)}")
                if not self.is_connected:
                    break
                time.sleep(1)  # Wait before retrying
                
        self.running = False

class OBDApp(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        
        # Initialize variables
        self.obd_connection = OBDConnection()
        self.obd_connection.connected.connect(self.on_connection_status_changed)
        self.obd_connection.data_received.connect(self.update_dashboard)
        self.obd_connection.dtc_received.connect(self.display_dtc)
        
        self.data_history = {
            "speed": deque([0] * GRAPH_HISTORY, maxlen=GRAPH_HISTORY),
            "rpm": deque([0] * GRAPH_HISTORY, maxlen=GRAPH_HISTORY),
            "engine_temp": deque([0] * GRAPH_HISTORY, maxlen=GRAPH_HISTORY),
            "fuel_level": deque([0] * GRAPH_HISTORY, maxlen=GRAPH_HISTORY),
            "intake_pressure": deque([0] * GRAPH_HISTORY, maxlen=GRAPH_HISTORY),
            # Vehicle-specific metrics will be added dynamically
        }
        
        self.time_axis = list(range(-GRAPH_HISTORY + 1, 1))
        self.current_data = {}
        self.log_data = []
        
        # Set up the UI
        self.init_ui()
        
        # Apply dark theme
        self.apply_dark_theme()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("OBD-II Diagnostic Tool")
        self.setGeometry(100, 100, 800, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Top section: Connection controls
        top_frame = QFrame()
        top_layout = QHBoxLayout()
        top_frame.setLayout(top_layout)
        
        # Vehicle selection
        self.vehicle_combo = QComboBox()
        self.vehicle_combo.addItem("Auto Detect")
        for vehicle in VEHICLE_PROFILES:
            self.vehicle_combo.addItem(vehicle)
        top_layout.addWidget(QLabel("Vehicle:"))
        top_layout.addWidget(self.vehicle_combo)
        
        # Connection status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet(f"color: {COLORS['error']}; font-size: 20px;")
        top_layout.addWidget(self.status_indicator)
        
        # Connection buttons
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setStyleSheet(self.get_button_style())
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        top_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setStyleSheet(self.get_button_style())
        self.disconnect_btn.clicked.connect(self.on_disconnect_clicked)
        self.disconnect_btn.setEnabled(False)
        top_layout.addWidget(self.disconnect_btn)
        
        # Diagnostic buttons
        self.read_dtc_btn = QPushButton("Read DTCs")
        self.read_dtc_btn.setStyleSheet(self.get_button_style())
        self.read_dtc_btn.clicked.connect(self.on_read_dtc_clicked)
        self.read_dtc_btn.setEnabled(False)
        top_layout.addWidget(self.read_dtc_btn)
        
        self.clear_dtc_btn = QPushButton("Clear DTCs")
        self.clear_dtc_btn.setStyleSheet(self.get_button_style())
        self.clear_dtc_btn.clicked.connect(self.on_clear_dtc_clicked)
        self.clear_dtc_btn.setEnabled(False)
        top_layout.addWidget(self.clear_dtc_btn)
        
        # Export button
        self.export_btn = QPushButton("Export Data")
        self.export_btn.setStyleSheet(self.get_button_style())
        self.export_btn.clicked.connect(self.on_export_clicked)
        self.export_btn.setEnabled(False)
        top_layout.addWidget(self.export_btn)
        
        main_layout.addWidget(top_frame)
        
        # Middle section: Tabs for Dashboard and Diagnostics
        self.tabs = QTabWidget()
        
        # Dashboard tab
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout()
        dashboard_widget.setLayout(dashboard_layout)
        
        # Metrics grid
        metrics_frame = QFrame()
        metrics_layout = QGridLayout()
        metrics_frame.setLayout(metrics_layout)
        
        # Standard metrics
        self.metric_labels = {}
        
        # Speed
        metrics_layout.addWidget(QLabel("Speed:"), 0, 0)
        self.metric_labels["speed"] = QLabel("0 km/h")
        self.metric_labels["speed"].setFont(QFont("Roboto", 14))
        metrics_layout.addWidget(self.metric_labels["speed"], 0, 1)
        
        # RPM
        metrics_layout.addWidget(QLabel("RPM:"), 0, 2)
        self.metric_labels["rpm"] = QLabel("0")
        self.metric_labels["rpm"].setFont(QFont("Roboto", 14))
        metrics_layout.addWidget(self.metric_labels["rpm"], 0, 3)
        
        # Engine Temperature
        metrics_layout.addWidget(QLabel("Engine Temp:"), 1, 0)
        self.metric_labels["engine_temp"] = QLabel("0 °C")
        self.metric_labels["engine_temp"].setFont(QFont("Roboto", 14))
        metrics_layout.addWidget(self.metric_labels["engine_temp"], 1, 1)
        
        # Fuel Level
        metrics_layout.addWidget(QLabel("Fuel Level:"), 1, 2)
        self.metric_labels["fuel_level"] = QLabel("0 %")
        self.metric_labels["fuel_level"].setFont(QFont("Roboto", 14))
        metrics_layout.addWidget(self.metric_labels["fuel_level"], 1, 3)
        
        # Intake Pressure
        metrics_layout.addWidget(QLabel("Intake Pressure:"), 2, 0)
        self.metric_labels["intake_pressure"] = QLabel("0 kPa")
        self.metric_labels["intake_pressure"].setFont(QFont("Roboto", 14))
        metrics_layout.addWidget(self.metric_labels["intake_pressure"], 2, 1)
        
        # Vehicle-specific metrics (will be populated dynamically)
        self.specific_metrics_row = 3
        
        dashboard_layout.addWidget(metrics_frame)
        
        # Graph selection
        graph_control_layout = QHBoxLayout()
        graph_control_layout.addWidget(QLabel("Graph:"))
        
        self.graph_combo = QComboBox()
        self.graph_combo.addItems(["Speed", "RPM", "Engine Temperature", "Fuel Level", "Intake Pressure"])
        self.graph_combo.currentTextChanged.connect(self.update_graph)
        graph_control_layout.addWidget(self.graph_combo)
        
        dashboard_layout.addLayout(graph_control_layout)
        
        # Graph
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground(COLORS["graph_background"])
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Set up the plot line
        pen = pg.mkPen(color=COLORS["graph_line"], width=2)
        self.plot_line = self.graph_widget.plot(self.time_axis, [0] * GRAPH_HISTORY, pen=pen)
        
        # Set labels and styles
        self.graph_widget.setLabel("left", "Value")
        self.graph_widget.setLabel("bottom", "Time (seconds)")
        
        # Style the axis
        axis_pen = pg.mkPen(color=COLORS["text"], width=1)
        self.graph_widget.getAxis("left").setPen(axis_pen)
        self.graph_widget.getAxis("bottom").setPen(axis_pen)
        
        dashboard_layout.addWidget(self.graph_widget)
        
        # Add dashboard tab
        self.tabs.addTab(dashboard_widget, "Dashboard")
        
        # Diagnostics tab
        diagnostics_widget = QWidget()
        diagnostics_layout = QVBoxLayout()
        diagnostics_widget.setLayout(diagnostics_layout)
        
        # DTC list
        self.dtc_list = QLabel("No DTCs found")
        self.dtc_list.setAlignment(Qt.AlignTop)
        self.dtc_list.setWordWrap(True)
        self.dtc_list.setStyleSheet(f"background-color: {COLORS['background']}; padding: 10px;")
        
        diagnostics_layout.addWidget(QLabel("Diagnostic Trouble Codes:"))
        diagnostics_layout.addWidget(self.dtc_list)
        
        # Add diagnostics tab
        self.tabs.addTab(diagnostics_widget, "Diagnostics")
        
        # Add tabs to main layout
        main_layout.addWidget(self.tabs)
        
        # Bottom section: Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Not connected")
        
        # Set up timer for graph updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(UPDATE_INTERVAL)
    
    def apply_dark_theme(self):
        """Apply dark theme to the application"""
        # Set application style
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                font-family: 'Roboto', sans-serif;
                font-size: 14px;
            }}
            
            QLabel {{
                color: {COLORS['text']};
            }}
            
            QTabWidget::pane {{
                border: 1px solid #3E4147;
                background-color: {COLORS['background']};
            }}
            
            QTabBar::tab {{
                background-color: #3E4147;
                color: {COLORS['text']};
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {COLORS['accent']};
            }}
            
            QComboBox {{
                background-color: #3E4147;
                color: {COLORS['text']};
                padding: 5px;
                border: 1px solid #3E4147;
                border-radius: 4px;
            }}
            
            QComboBox::drop-down {{
                border: 0px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: #3E4147;
                color: {COLORS['text']};
                selection-background-color: {COLORS['accent']};
            }}
            
            QStatusBar {{
                background-color: #3E4147;
                color: {COLORS['text']};
            }}
            
            QFrame {{
                border: 1px solid #3E4147;
                border-radius: 4px;
            }}
        """)
    
    def get_button_style(self):
        """Get the style for buttons"""
        return f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: {COLORS['text']};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
            
            QPushButton:disabled {{
                background-color: #3E4147;
                color: #8E9297;
            }}
        """
    
    def on_connect_clicked(self):
        """Handle connect button click"""
        # Get selected vehicle profile
        vehicle_index = self.vehicle_combo.currentIndex()
        if vehicle_index > 0:
            self.obd_connection.vehicle_profile = self.vehicle_combo.currentText()
        else:
            self.obd_connection.vehicle_profile = None
        
        # Update UI
        self.connect_btn.setEnabled(False)
        self.status_bar.showMessage("Connecting...")
        
        # Connect in a separate thread
        threading.Thread(target=self.connect_thread).start()
    
    def connect_thread(self):
        """Connect to OBD in a separate thread"""
        success = self.obd_connection.connect_obd()
        if success:
            # Start the data polling thread
            self.obd_connection.start()
            
            # Set up vehicle-specific metrics if a profile is selected
            if self.obd_connection.vehicle_profile:
                self.setup_vehicle_specific_metrics(self.obd_connection.vehicle_profile)
    
    def on_disconnect_clicked(self):
        """Handle disconnect button click"""
        self.obd_connection.disconnect_obd()
        
        # Update UI
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.read_dtc_btn.setEnabled(False)
        self.clear_dtc_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.status_indicator.setStyleSheet(f"color: {COLORS['error']}; font-size: 20px;")
        self.status_bar.showMessage("Disconnected")
        
        # Clear vehicle-specific metrics
        self.clear_vehicle_specific_metrics()
    
    def on_read_dtc_clicked(self):
        """Handle read DTCs button click"""
        self.status_bar.showMessage("Reading DTCs...")
        threading.Thread(target=self.obd_connection.read_dtc).start()
    
    def on_clear_dtc_clicked(self):
        """Handle clear DTCs button click"""
        reply = QMessageBox.question(
            self, 
            "Clear DTCs", 
            "Are you sure you want to clear all diagnostic trouble codes?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.status_bar.showMessage("Clearing DTCs...")
            
            def clear_thread():
                success = self.obd_connection.clear_dtc()
                if success:
                    self.status_bar.showMessage("DTCs cleared successfully")
                    self.dtc_list.setText("No DTCs found")
                else:
                    self.status_bar.showMessage("Failed to clear DTCs")
            
            threading.Thread(target=clear_thread).start()
    
    def on_export_clicked(self):
        """Handle export data button click"""
        if not self.log_data:
            QMessageBox.warning(self, "Export Data", "No data available to export")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Data", 
            f"obd_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='') as csvfile:
                    # Get all possible field names from the log data
                    fieldnames = ["timestamp"]
                    for entry in self.log_data:
                        for key in entry.keys():
                            if key != "timestamp" and key not in fieldnames:
                                fieldnames.append(key)
                    
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for entry in self.log_data:
                        writer.writerow(entry)
                
                self.status_bar.showMessage(f"Data exported to {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")
    
    def on_connection_status_changed(self, connected, message):
        """Handle connection status changes"""
        if connected:
            self.status_indicator.setStyleSheet(f"color: {COLORS['success']}; font-size: 20px;")
            self.status_bar.showMessage("Connected: " + message.split("\n")[0])
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.read_dtc_btn.setEnabled(True)
            self.clear_dtc_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            
            # Show connection details in a message box
            QMessageBox.information(self, "Connection Successful", message)
        else:
            self.status_indicator.setStyleSheet(f"color: {COLORS['error']}; font-size: 20px;")
            self.status_bar.showMessage("Connection failed: " + message)
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.read_dtc_btn.setEnabled(False)
            self.clear_dtc_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            
            # Show error in a message box
            QMessageBox.critical(self, "Connection Failed", message)
    
    def setup_vehicle_specific_metrics(self, vehicle_profile):
        """Set up vehicle-specific metrics based on the selected profile"""
        # Clear existing vehicle-specific metrics
        self.clear_vehicle_specific_metrics()
        
        # Add new vehicle-specific metrics
        if vehicle_profile in VEHICLE_PROFILES:
            specific_pids = VEHICLE_PROFILES[vehicle_profile]["specific_pids"]
            
            metrics_layout = self.findChild(QGridLayout)
            row = self.specific_metrics_row
            
            for i, (name, pid) in enumerate(specific_pids.items()):
                col = i % 2 * 2  # Alternate between columns 0 and 2
                if i > 0 and i % 2 == 0:
                    row += 1
                
                metrics_layout.addWidget(QLabel(f"{name}:"), row, col)
                
                metric_key = name.lower().replace(" ", "_")
                self.metric_labels[metric_key] = QLabel("0")
                self.metric_labels[metric_key].setFont(QFont("Roboto", 14))
                metrics_layout.addWidget(self.metric_labels[metric_key], row, col + 1)
                
                # Add to data history
                self.data_history[metric_key] = deque([0] * GRAPH_HISTORY, maxlen=GRAPH_HISTORY)
                
                # Add to graph combo
                self.graph_combo.addItem(name)
    
    def clear_vehicle_specific_metrics(self):
        """Clear vehicle-specific metrics"""
        metrics_layout = self.findChild(QGridLayout)
        
        # Remove vehicle-specific labels
        for key in list(self.metric_labels.keys()):
            if key not in ["speed", "rpm", "engine_temp", "fuel_level", "intake_pressure"]:
                if key in self.data_history:
                    del self.data_history[key]
                
                if key in self.metric_labels:
                    # Remove from layout and delete
                    metrics_layout.removeWidget(self.metric_labels[key])
                    self.metric_labels[key].deleteLater()
                    del self.metric_labels[key]
        
        # Reset graph combo to standard metrics only
        self.graph_combo.clear()
        self.graph_combo.addItems(["Speed", "RPM", "Engine Temperature", "Fuel Level", "Intake Pressure"])
    
    def update_dashboard(self, data):
        """Update dashboard with new data"""
        self.current_data = data
        
        # Add timestamp to data for logging
        log_entry = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        log_entry.update(data)
        self.log_data.append(log_entry)
        
        # Update metric labels
        if "speed" in data and data["speed"] is not None:
            self.metric_labels["speed"].setText(f"{data['speed']:.1f} km/h")
            self.data_history["speed"].append(data["speed"])
        
        if "rpm" in data and data["rpm"] is not None:
            self.metric_labels["rpm"].setText(f"{data['rpm']:.0f}")
            self.data_history["rpm"].append(data["rpm"])
        
        if "engine_temp" in data and data["engine_temp"] is not None:
            self.metric_labels["engine_temp"].setText(f"{data['engine_temp']:.1f} °C")
            self.data_history["engine_temp"].append(data["engine_temp"])
        
        if "fuel_level" in data and data["fuel_level"] is not None:
            self.metric_labels["fuel_level"].setText(f"{data['fuel_level']:.1f} %")
            self.data_history["fuel_level"].append(data["fuel_level"])
        
        if "intake_pressure" in data and data["intake_pressure"] is not None:
            self.metric_labels["intake_pressure"].setText(f"{data['intake_pressure']:.1f} kPa")
            self.data_history["intake_pressure"].append(data["intake_pressure"])
        
        # Update vehicle-specific metrics
        for key, value in data.items():
            if key not in ["speed", "rpm", "engine_temp", "fuel_level", "intake_pressure"] and value is not None:
                if key in self.metric_labels:
                    # Determine the unit based on the key
                    unit = ""
                    if "pressure" in key or "boost" in key:
                        unit = " kPa"
                    elif "temp" in key:
                        unit = " °C"
                    elif "level" in key or "battery" in key:
                        unit = " %"
                    elif "consumption" in key:
                        unit = " L/100km"
                    elif "status" in key:
                        unit = " (0=off, 1=on)"
                    
                    self.metric_labels[key].setText(f"{value:.1f}{unit}")
                    
                    if key in self.data_history:
                        self.data_history[key].append(value)
        
        # Update graph
        self.update_graph()
    
    def update_graph(self):
        """Update the graph with current data"""
        current_graph = self.graph_combo.currentText().lower().replace(" ", "_")
        
        # Map display names to data keys
        if current_graph == "engine_temperature":
            current_graph = "engine_temp"
        
        if current_graph in self.data_history:
            self.plot_line.setData(self.time_axis, list(self.data_history[current_graph]))
            
            # Set appropriate Y axis range
            if current_graph == "rpm":
                self.graph_widget.setYRange(0, max(max(self.data_history[current_graph]), 1000))
            elif current_graph == "speed":
                self.graph_widget.setYRange(0, max(max(self.data_history[current_graph]), 60))
            elif current_graph == "engine_temp":
                self.graph_widget.setYRange(0, max(max(self.data_history[current_graph]), 100))
            elif current_graph == "fuel_level":
                self.graph_widget.setYRange(0, 100)
            else:
                # Auto range for other metrics
                max_val = max(self.data_history[current_graph])
                if max_val > 0:
                    self.graph_widget.setYRange(0, max_val * 1.2)
                else:
                    self.graph_widget.setYRange(0, 100)
    
    def display_dtc(self, dtc_codes):
        """Display diagnostic trouble codes"""
        if not dtc_codes:
            self.dtc_list.setText("No DTCs found")
            return
            
        dtc_text = "<table width='100%' cellspacing='0' cellpadding='5' style='border: 1px solid #3E4147;'>"
        dtc_text += "<tr style='background-color: #3E4147;'><th>Code</th><th>Description</th></tr>"
        
        for i, (code, description) in enumerate(dtc_codes):
            bg_color = "#2C2F33" if i % 2 == 0 else "#3E4147"
            dtc_text += f"<tr style='background-color: {bg_color};'><td>{code}</td><td>{description}</td></tr>"
        
        dtc_text += "</table>"
        self.dtc_list.setText(dtc_text)
        
        # Switch to diagnostics tab
        self.tabs.setCurrentIndex(1)
        
        # Update status bar
        self.status_bar.showMessage(f"Found {len(dtc_codes)} diagnostic trouble codes")

def main():
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont("Roboto", 10)
    app.setFont(font)
    
    # Create and show the main window
    window = OBDApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
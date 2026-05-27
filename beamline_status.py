"""
Beamline Status and Control Screen
PyDM-based screen with device status indicators and navigation tabs
"""
from pydm import Display
from qtpy.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor
from pydm.widgets import PyDMDrawingCircle, PyDMLabel
import subprocess
import os


class DeviceIndicator(QFrame):
    """Widget showing status of a single device with multiple indicators"""
    
    def __init__(self, device_name, pv_prefix, num_indicators=3, parent=None):
        super().__init__(parent)
        self.device_name = device_name
        self.pv_prefix = pv_prefix
        self.num_indicators = num_indicators
        self.setup_ui()
    
    def setup_ui(self):
        """Create the device indicator UI"""
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setLineWidth(1)
        self.setMinimumWidth(80)
        
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)
        
        # Device name label
        name_label = QLabel(self.device_name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-weight: bold; font-size: 9pt;")
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Status indicator circles
        indicators_layout = QHBoxLayout()
        indicators_layout.setSpacing(3)
        indicators_layout.setAlignment(Qt.AlignCenter)
        
        self.indicators = []
        for i in range(self.num_indicators):
            indicator = PyDMDrawingCircle()
            
            # Set channel - adjust the PV naming to match your system
            pv_name = f"ca://{self.pv_prefix}:Status{i}"
            indicator.channel = pv_name
            
            # Configure the indicator appearance
            indicator.setFixedSize(15, 15)
            
            # Set up color rules for connected/disconnected states
            # When disconnected, show gray
            indicator.brush = QColor(150, 150, 150)  # Default gray
            
            # Optional: Print debug info
            print(f"Created indicator for: {pv_name}")
            
            self.indicators.append(indicator)
            indicators_layout.addWidget(indicator)
        
        layout.addLayout(indicators_layout)
        
        # Optional: Status text label
        status_label = PyDMLabel()
        status_label.channel = f"ca://{self.pv_prefix}:State"
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("font-size: 7pt; color: #666;")
        status_label.setMaximumHeight(20)
        # Show disconnected state
        status_label.showUnits = False
        layout.addWidget(status_label)


class BeamlineStatusScreen(Display):
    """Main beamline status and navigation screen"""
    
    def __init__(self, parent=None, args=None, macros=None):
        super().__init__(parent=parent, args=args, macros=macros)
        
        # Device configuration - REPLACE THESE WITH YOUR ACTUAL PV PREFIXES
        # Example format: ("Display Name", "PV:PREFIX")
        self.devices_config = {
            'detectors': [
                ("DG1", "XCS:DG1"),        # Replace with actual PV
                ("HXX", "XCS:HXX"),
                ("MXT/DVD", "XCS:MXTDVD"),
                ("DG2", "XCS:DG2"),
                ("MON", "XCS:MON"),
                ("DG3", "XCS:DG3"),
            ],
            'cameras': [
                ("DIA", "XCS:CAM:DIA"),
                ("SB1", "XCS:CAM:SB1"),
                ("S&D", "XCS:CAM:SD"),
                ("SB2", "XCS:CAM:SB2"),
                ("EPIX", "XCS:CAM:EPIX"),
                ("GDN", "XCS:CAM:GDN"),
                ("USER", "XCS:CAM:USER"),
                ("LAM", "XCS:CAM:LAM"),
            ],
            'motors': [
                ("Motor1", "XCS:MOT:M1"),
                ("Motor2", "XCS:MOT:M2"),
                ("Motor3", "XCS:MOT:M3"),
            ],
        }
        
        # Screen file mappings for navigation buttons
        self.screen_files = {
            # LCLS Tab
            'btnWebCameras': 'web_cameras.ui',
            'btnViewerBeamline': 'viewer_beamline.ui',
            'btnViewerXCS': 'viewer_xcs.ui',
            'btnViewerUserGige': 'viewer_user_gige.ui',
            
            # Laser Tab
            'btnLaserControl': 'laser_control.ui',
            
            # Detectors Tab
            'btnEpix1': 'epix1.ui',
            'btnEpix2': 'epix2.ui',
            'btnEpix3': 'epix3.ui',
            'btnEpix4': 'epix4.ui',
            'btnDETHMPJungfrau': 'det_hmp_jungfrau.ui',
            'btnDETHMPs': 'det_hmps.ui',
            'btnDETChillers': 'det_chillers.ui',
            
            # User Tab
            'btnUserDiagnostics': 'user_diagnostics.ui',
            
            # Beamline Tab
            'btnBeamlineOverview': 'beamline_overview.ui',
            
            # Favorites Tab
            'btnFavorite1': 'favorite1.ui',
        }
    
    def ui_filename(self):
        """Return the path to the UI file"""
        return 'beamline_status.ui'
    
    def ui_filepath(self):
        """Return the full path to the UI file"""
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                           self.ui_filename())
    
    def setup_ui(self):
        """Called after UI file is loaded - customize the display here"""
        print("Setting up UI...")
        
        # Populate the device status area
        self.populate_device_status()
        
        # Connect all navigation buttons
        self.connect_navigation_buttons()
        
        # Apply custom styling
        self.apply_styling()
        
        print("UI setup complete")
    
    def populate_device_status(self):
        """Populate the device status grid with indicators"""
        print("Populating device status grid...")
        
        # Access the grid layout from the loaded UI
        grid_layout = self.deviceStatusGrid
        
        # Clear any existing widgets
        while grid_layout.count():
            item = grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        col = 0
        row = 0
        max_cols = 7  # Match your screenshot layout
        
        # Add all device categories
        for category, devices in self.devices_config.items():
            print(f"Adding {category} devices...")
            for device_name, pv_prefix in devices:
                indicator = DeviceIndicator(device_name, pv_prefix)
                grid_layout.addWidget(indicator, row, col)
                print(f"  Added {device_name} at ({row}, {col})")
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
        
        # Add stretch to remaining space
        grid_layout.setRowStretch(row + 1, 1)
        grid_layout.setColumnStretch(max_cols, 1)
        
        print(f"Device status grid populated with {len([d for devices in self.devices_config.values() for d in devices])} devices")
    
    def connect_navigation_buttons(self):
        """Connect all navigation buttons to open their respective screens"""
        for button_name, screen_file in self.screen_files.items():
            button = getattr(self, button_name, None)
            if button:
                button.clicked.connect(
                    lambda checked, f=screen_file: self.open_screen(f)
                )
            else:
                print(f"Warning: Button {button_name} not found in UI")
    
    def open_screen(self, screen_file):
        """
        Open a new screen window
        
        Parameters
        ----------
        screen_file : str
            Name of the screen file to open
        """
        screens_dir = os.path.join(os.path.dirname(__file__), 'screens')
        screen_path = os.path.join(screens_dir, screen_file)
        
        if not os.path.exists(screen_path):
            print(f"Warning: Screen file not found: {screen_path}")
            print(f"Would open: {screen_file}")
            return
        
        try:
            subprocess.Popen(['pydm', screen_path])
            print(f"Opened screen: {screen_file}")
        except Exception as e:
            print(f"Error opening screen {screen_file}: {e}")
    
    def apply_styling(self):
        """Apply custom styling to widgets"""
        
        # Style the tab widget - make tabs wider
        self.navigationTabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #555;
                background: #f0f0f0;
            }
            QTabBar::tab {
                background: #ddd;
                padding: 10px 40px;
                margin: 2px;
                font-size: 12pt;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: #8b008b;
                color: white;
                font-weight: bold;
            }
        """)
        
        # Style all QPushButtons in the tabs
        button_style = """
            QPushButton {
                background-color: #e0e0e0;
                border: 2px solid #999;
                border-radius: 5px;
                padding: 10px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
                border-color: #666;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """
        
        # Apply to all buttons
        for button_name in self.screen_files.keys():
            button = getattr(self, button_name, None)
            if button:
                button.setStyleSheet(button_style)


if __name__ == '__main__':
    import sys
    from pydm import PyDMApplication
    
    app = PyDMApplication(use_main_window=False)
    main_window = BeamlineStatusScreen()
    main_window.show()
    sys.exit(app.exec_())

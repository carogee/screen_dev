from pydm import Display
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTabWidget, QGridLayout, QLabel, QFrame)
from PyQt5.QtCore import Qt
from pydm.widgets import PyDMLabel, PyDMDrawingCircle
from pydm import Display
import subprocess
import os

class BeamlineStatusScreen(Display):
    def __init__(self, parent=None, args=None):
        super(BeamlineStatusScreen, self).__init__(parent=parent, args=args)
        
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Top section - Status display
        status_section = self.create_status_section()
        main_layout.addWidget(status_section, stretch=7)
        
        # Bottom section - Tabs with buttons
        tab_section = self.create_tab_section()
        main_layout.addWidget(tab_section, stretch=3)
        
        self.setWindowTitle("Beamline Control")
        
    def create_status_section(self):
        """Create the top status display area"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        layout = QVBoxLayout()
        frame.setLayout(layout)
        
        # Add your synoptic diagram here
        # This would typically be a PyDMDrawing or custom widget
        status_label = QLabel("Beamline Status Display Area")
        status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_label)
        
        # Example: Add some status indicators
        status_grid = QGridLayout()
        
        # Example devices with PV indicators
        devices = [
            ("DG1", "YOUR:PREFIX:DG1"),
            ("DG2", "YOUR:PREFIX:DG2"),
            ("MON", "YOUR:PREFIX:MON"),
            ("DG3", "YOUR:PREFIX:DG3"),
        ]
        
        for i, (name, pv_base) in enumerate(devices):
            label = QLabel(name)
            status_grid.addWidget(label, 0, i)
            
            # Status indicator (green/red circle)
            indicator = PyDMDrawingCircle()
            indicator.setProperty("channel", f"ca://{pv_base}:Status")
            indicator.setFixedSize(20, 20)
            status_grid.addWidget(indicator, 1, i)
        
        layout.addLayout(status_grid)
        
        return frame
    
    def create_tab_section(self):
        """Create the bottom tabbed section with buttons"""
        tab_widget = QTabWidget()
        
        # Define tabs and their buttons
        tabs_config = {
            "LCLS": [
                ("Web Cameras", "web_cameras.ui"),
                ("Viewer - Beamline", "viewer_beamline.ui"),
                ("Viewer - XCS", "viewer_xcs.ui"),
                ("Viewer - User Gige", "viewer_user_gige.ui"),
            ],
            "Laser": [],  # Add laser tab buttons here
            "Detectors": [
                ("epix1", "epix1.ui"),
                ("epix2", "epix2.ui"),
                ("epix3", "epix3.ui"),
                ("epix4", "epix4.ui"),
                ("DET HMP (Jungfrau)", "det_hmp_jungfrau.ui"),
                ("DET HMPs", "det_hmps.ui"),
                ("DET Chillers", "det_chillers.ui"),
            ],
            "User": [],
            "Beamline": [],
            "Favorites": [],
        }
        
        # Create tabs
        for tab_name, buttons in tabs_config.items():
            tab = self.create_tab_content(buttons)
            tab_widget.addTab(tab, tab_name)
        
        # Set default tab
        tab_widget.setCurrentIndex(2)  # Detectors tab
        
        return tab_widget
    
    def create_tab_content(self, buttons_config):
        """Create content for each tab with buttons"""
        widget = QWidget()
        layout = QGridLayout()
        widget.setLayout(layout)
        
        # Arrange buttons in grid (3 columns)
        cols = 3
        for i, (button_text, ui_file) in enumerate(buttons_config):
            row = i // cols
            col = i % cols
            
            button = QPushButton(button_text)
            button.clicked.connect(lambda checked, f=ui_file: self.open_screen(f))
            button.setMinimumHeight(40)
            layout.addWidget(button, row, col)
        
        layout.setRowStretch(layout.rowCount(), 1)
        
        return widget
    
    def open_screen(self, ui_file):
        """Open a new PyDM screen window"""
        # Method 1: Using pydm executable
        ui_path = os.path.join("ui", ui_file)
        subprocess.Popen(["pydm", ui_path])
        
        # Method 2: Open within the application (alternative)
        # from pydm import Display
        # new_window = Display(parent=None, ui_filename=ui_path)
        # new_window.show()

    def ui_filename(self):
        # If you prefer to use a .ui file for the main layout
        return None  # or return "path/to/main.ui"

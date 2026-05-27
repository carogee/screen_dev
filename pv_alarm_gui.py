# cd /cds/home/s/sanghoon/code/python_gui_tools/
import sys
import os
import time
import subprocess
from datetime import datetime
from qtpy.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QLabel, QLineEdit, QPushButton)
from qtpy.QtCore import QTimer
import pyqtgraph as pg
import numpy as np
from epics import caget

# Disable OpenGL to avoid graphics issues
os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'
pg.setConfigOptions(useOpenGL=False)
pg.setConfigOptions(antialias=True)


class PVAlarmDisplay(QWidget):
    def __init__(self, parent=None):
        super(PVAlarmDisplay, self).__init__(parent=parent)
        self.setup_ui()
        
        # Monitoring Variables
        self.monitoring = False
        self.time_vals = []
        self.data_vals = []
        self.blink_state = False
        self.out_of_range_start_time = None
        self.alarm_active = False
        self.alarm_paused = False
        
        # Default values
        self.scale = 1.0
        self.offset = 0.0
        self.alarm_delay = 1
        self.time_window = 100
        self.show_threshold = True
        
        # Timer for updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_gui)
        self.update_timer.start(500)  # 500ms update interval
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("EPICS PV Alarm with Time Trace")
        self.resize(900, 700)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # -----------------------------
        # Form Layout
        # -----------------------------
        form_layout = QGridLayout()
        
        # PV Entry
        form_layout.addWidget(QLabel("EPICS PV:"), 0, 0)
        self.pv_entry = QLineEdit()
        self.pv_entry.setMinimumWidth(300)
        form_layout.addWidget(self.pv_entry, 0, 1, 1, 3)
        
        # Scale / Offset
        form_layout.addWidget(QLabel("Scale:"), 1, 0)
        self.scale_entry = QLineEdit("1.0")
        self.scale_entry.setMaximumWidth(100)
        form_layout.addWidget(self.scale_entry, 1, 1)
        
        form_layout.addWidget(QLabel("Offset:"), 1, 2)
        self.offset_entry = QLineEdit("0.0")
        self.offset_entry.setMaximumWidth(100)
        form_layout.addWidget(self.offset_entry, 1, 3)
        
        # Low / High Limits
        form_layout.addWidget(QLabel("Low Limit:"), 2, 0)
        self.low_entry = QLineEdit()
        self.low_entry.setMaximumWidth(100)
        form_layout.addWidget(self.low_entry, 2, 1)
        
        form_layout.addWidget(QLabel("High Limit:"), 2, 2)
        self.high_entry = QLineEdit()
        self.high_entry.setMaximumWidth(100)
        form_layout.addWidget(self.high_entry, 2, 3)
        
        # Alarm Delay & Time Window
        form_layout.addWidget(QLabel("Alarm Delay (sec):"), 3, 0)
        self.alarm_delay_entry = QLineEdit("1")
        self.alarm_delay_entry.setMaximumWidth(100)
        form_layout.addWidget(self.alarm_delay_entry, 3, 1)
        
        form_layout.addWidget(QLabel("Time Window (sec):"), 3, 2)
        self.time_window_entry = QLineEdit("100")
        self.time_window_entry.setMaximumWidth(100)
        form_layout.addWidget(self.time_window_entry, 3, 3)
        
        main_layout.addLayout(form_layout)
        
        # Control Buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start\nMonitoring")
        self.start_button.setStyleSheet("background-color: lightgreen; min-height: 40px;")
        self.start_button.clicked.connect(self.start_monitor)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop\nMonitoring")
        self.stop_button.setStyleSheet("background-color: salmon; min-height: 40px;")
        self.stop_button.clicked.connect(self.stop_monitor)
        button_layout.addWidget(self.stop_button)
        
        self.threshold_button = QPushButton("Hide Limit Lines")
        self.threshold_button.clicked.connect(self.toggle_threshold_lines)
        button_layout.addWidget(self.threshold_button)
        
        self.alarm_pause_button = QPushButton("Pause Alarm")
        self.alarm_pause_button.clicked.connect(self.toggle_alarm_pause)
        button_layout.addWidget(self.alarm_pause_button)
        
        self.reset_button = QPushButton("Reset Plot")
        self.reset_button.setStyleSheet("background-color: lightblue;")
        self.reset_button.clicked.connect(self.reset_plot)
        button_layout.addWidget(self.reset_button)
        
        self.quit_button = QPushButton("Close GUI")
        self.quit_button.setStyleSheet("background-color: lightgray;")
        self.quit_button.clicked.connect(self.close)
        button_layout.addWidget(self.quit_button)
        
        main_layout.addLayout(button_layout)
        
        # Status Label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: blue; padding: 5px; font-weight: bold;")
        main_layout.addWidget(self.status_label)
        
        # -----------------------------
        # Plot Widget (using pyqtgraph)
        # -----------------------------
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'PV Value')
        self.plot_widget.setLabel('bottom', 'Time (seconds)')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setBackground('w')
        
        # Plot line for data
        self.plot_line = self.plot_widget.plot([], [], pen=pg.mkPen('b', width=2), 
                                               symbol='o', symbolSize=5, symbolBrush='b')
        
        # Threshold lines - initially hidden until values are set
        self.low_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('r', width=2, style=pg.QtCore.Qt.DashLine),
                                       movable=False, label='Low Limit')
        self.high_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('r', width=2, style=pg.QtCore.Qt.DashLine),
                                        movable=False, label='High Limit')
        
        self.plot_widget.addItem(self.low_line)
        self.plot_widget.addItem(self.high_line)
        
        # Initially hide threshold lines
        self.low_line.hide()
        self.high_line.hide()
        
        main_layout.addWidget(self.plot_widget)
        
        self.setLayout(main_layout)
    
    def start_monitor(self):
        """Start monitoring the PV"""
        if not self.monitoring:
            self.monitoring = True
            self.status_label.setText("Monitoring started.")
            self.status_label.setStyleSheet("color: green; padding: 5px; font-weight: bold;")
    
    def stop_monitor(self):
        """Stop monitoring the PV"""
        self.monitoring = False
        self.status_label.setText("Monitoring stopped.")
        self.status_label.setStyleSheet("color: black; padding: 5px; font-weight: bold;")
        self.reset_plot_background()
        self.out_of_range_start_time = None
        self.alarm_active = False
    
    def toggle_threshold_lines(self):
        """Toggle visibility of threshold lines"""
        self.show_threshold = not self.show_threshold
        if self.show_threshold:
            self.threshold_button.setText("Hide Limit Lines")
        else:
            self.threshold_button.setText("Show Limit Lines")
        self.update_threshold_visibility()
    
    def update_threshold_visibility(self):
        """Update threshold line visibility based on settings"""
        # Only show if toggle is on AND valid limits are set
        try:
            low = float(self.low_entry.text())
            if self.show_threshold and not np.isnan(low) and not np.isinf(low):
                self.low_line.setPos(low)
                self.low_line.show()
            else:
                self.low_line.hide()
        except (ValueError, AttributeError):
            self.low_line.hide()
        
        try:
            high = float(self.high_entry.text())
            if self.show_threshold and not np.isnan(high) and not np.isinf(high):
                self.high_line.setPos(high)
                self.high_line.show()
            else:
                self.high_line.hide()
        except (ValueError, AttributeError):
            self.high_line.hide()
    
    def toggle_alarm_pause(self):
        """Toggle alarm pause state"""
        self.alarm_paused = not self.alarm_paused
        if self.alarm_paused:
            self.alarm_pause_button.setText("Resume Alarm")
        else:
            self.alarm_pause_button.setText("Pause Alarm")
            self.alarm_active = False
    
    def reset_plot(self):
        """Clear all plot data"""
        self.time_vals.clear()
        self.data_vals.clear()
        self.plot_line.setData([], [])
        self.status_label.setText("Plot reset.")
        self.status_label.setStyleSheet("color: black; padding: 5px; font-weight: bold;")
        self.reset_plot_background()
    
    def play_alert_sound(self):
        """Play alert sound"""
        if self.alarm_paused:
            return
        try:
            subprocess.Popen(["paplay", "/cds/home/s/sanghoon/code/python_gui_tools/sounds/pv_alarm.oga"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    
    def reset_plot_background(self):
        """Reset plot background to white"""
        self.plot_widget.setBackground('w')
    
    def update_gui(self):
        """Main update loop for monitoring and plotting"""
        if not self.monitoring:
            return
        
        pv = self.pv_entry.text().strip()
        if not pv:
            return
        
        try:
            # Get parameter values
            self.scale = float(self.scale_entry.text())
            self.offset = float(self.offset_entry.text())
            self.alarm_delay = int(self.alarm_delay_entry.text())
            self.time_window = float(self.time_window_entry.text())
            
            # Validate parameters
            if np.isnan(self.scale) or np.isnan(self.offset):
                raise ValueError("Scale or offset is NaN")
            
            # Read PV value
            raw_val = caget(pv, timeout=1.0)
            if raw_val is None:
                raise ValueError("PV read returned None")
            
            # Check for NaN or inf in raw value
            if np.isnan(raw_val) or np.isinf(raw_val):
                raise ValueError(f"PV value is invalid: {raw_val}")
            
            val = raw_val * self.scale + self.offset
            
            # Final check
            if np.isnan(val) or np.isinf(val):
                raise ValueError(f"Calculated value is invalid: {val}")
            
        except Exception as e:
            self.status_label.setText(f"PV read error: {str(e)}")
            self.status_label.setStyleSheet("color: orange; padding: 5px; font-weight: bold;")
            return
        
        # Append data
        current_time = datetime.now()
        self.time_vals.append(current_time.timestamp())
        self.data_vals.append(val)
        
        # Apply time window
        cutoff = current_time.timestamp() - self.time_window
        while self.time_vals and self.time_vals[0] < cutoff:
            self.time_vals.pop(0)
            self.data_vals.pop(0)
        
        # Update plot only if we have valid data
        if self.time_vals and self.data_vals:
            try:
                # Convert timestamps to relative time for better display
                times_array = np.array(self.time_vals)
                data_array = np.array(self.data_vals)
                
                # Verify no NaN/inf in arrays
                if np.any(np.isnan(times_array)) or np.any(np.isnan(data_array)):
                    raise ValueError("NaN detected in plot data")
                
                times_relative = times_array - times_array[0]
                self.plot_line.setData(times_relative, data_array)
            except Exception as e:
                print(f"Plot update error: {e}")
        
        # Update threshold lines
        try:
            low = float(self.low_entry.text())
        except ValueError:
            low = float("-inf")
        
        try:
            high = float(self.high_entry.text())
        except ValueError:
            high = float("inf")
        
        # Update threshold line visibility
        self.update_threshold_visibility()
        
        # Alarm logic
        out_of_range = (val < low or val > high)
        now = time.time()
        
        if out_of_range:
            if self.out_of_range_start_time is None:
                self.out_of_range_start_time = now
                self.alarm_active = False
            
            elapsed = now - self.out_of_range_start_time
            self.status_label.setText(
                f"OUT of Range: {val:.3f} (raw={raw_val:.3f}) [{elapsed:.1f}s] (Delay {self.alarm_delay}s)"
            )
            self.status_label.setStyleSheet("color: red; padding: 5px; font-weight: bold;")
            
            if elapsed >= self.alarm_delay and not self.alarm_paused:
                if not self.alarm_active:
                    self.status_label.setText(
                        f"ALARM: Value={val:.3f}, raw={raw_val:.3f} (Persistent > {self.alarm_delay}s)"
                    )
                    self.status_label.setStyleSheet("color: white; background-color: red; padding: 5px; font-weight: bold;")
                    self.play_alert_sound()
                    self.alarm_active = True
                
                # Background blink
                color = 'r' if not self.blink_state else 'darkgreen'
                self.plot_widget.setBackground(color)
                self.blink_state = not self.blink_state
            else:
                self.reset_plot_background()
        else:
            self.status_label.setText(f"Value={val:.3f} (Normal), raw={raw_val:.3f}")
            self.status_label.setStyleSheet("color: blue; padding: 5px; font-weight: bold;")
            self.reset_plot_background()
            self.out_of_range_start_time = None
            self.blink_state = False
            self.alarm_active = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    display = PVAlarmDisplay()
    display.show()
    sys.exit(app.exec_())

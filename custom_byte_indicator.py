from pydm.widgets.byte import PyDMByteIndicator
from qtpy.QtGui import QPainter, QFont, QPen, QColor
from qtpy.QtCore import Qt, QRectF, Property
from qtpy.QtWidgets import QWidget


class SymbolOverlay(QWidget):
    """Transparent overlay to draw symbols on top of everything"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._byte_indicator = parent
        self._show_symbols = True
    
    def paintEvent(self, event):
        if not self._show_symbols or not self._byte_indicator:
            return
        
        if not self._byte_indicator.circles:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # Get current value
        try:
            if self._byte_indicator._shift < 0:
                value = int(self._byte_indicator.value) << abs(self._byte_indicator._shift)
            else:
                value = int(self._byte_indicator.value) >> self._byte_indicator._shift
        except (TypeError, ValueError):
            value = 0
        
        # Calculate layout
        num_bits = self._byte_indicator.numBits
        
        if self._byte_indicator._show_labels:
            widget_height = self.height() - self._byte_indicator._label_height
            widget_width = self.width()
        else:
            widget_height = self.height()
            widget_width = self.width()
        
        # Font setup
        font = QFont()
        font.setFamily("Arial")
        font.setBold(True)
        
        if self._byte_indicator._orientation == Qt.Horizontal:
            spacing = widget_width / num_bits
            circle_diameter = min(spacing * 0.8, widget_height * 0.8)
            font_size = max(10, int(circle_diameter * 0.6))
            font.setPointSize(font_size)
            painter.setFont(font)
            
            for i in range(num_bits):
                bit_val = bool((value >> i) & 1)
                x_center = (i + 0.5) * spacing
                y_center = widget_height / 2
                
                # Checkmark for green (on), X for red (off)
                symbol = "✓" if bit_val else "✕"
                
                painter.setPen(QPen(QColor(255, 255, 255), 3))
                text_rect = QRectF(
                    x_center - circle_diameter/2,
                    y_center - circle_diameter/2,
                    circle_diameter,
                    circle_diameter
                )
                painter.drawText(text_rect, Qt.AlignCenter | Qt.AlignVCenter, symbol)
        else:  # Vertical
            spacing = widget_height / num_bits
            circle_diameter = min(spacing * 0.8, widget_width * 0.8)
            font_size = max(10, int(circle_diameter * 0.6))
            font.setPointSize(font_size)
            painter.setFont(font)
            
            for i in range(num_bits):
                bit_val = bool((value >> i) & 1)
                x_center = widget_width / 2
                y_center = (i + 0.5) * spacing
                
                # Checkmark for green (on), X for red (off)
                symbol = "✓" if bit_val else "✕"
                
                painter.setPen(QPen(QColor(255, 255, 255), 3))
                text_rect = QRectF(
                    x_center - circle_diameter/2,
                    y_center - circle_diameter/2,
                    circle_diameter,
                    circle_diameter
                )
                painter.drawText(text_rect, Qt.AlignCenter | Qt.AlignVCenter, symbol)
        
        painter.end()


class PyDMByteIndicatorWithSymbols(PyDMByteIndicator):
    """
    PyDMByteIndicator with checkmark/X symbols overlay on circles
    """
    def __init__(self, parent=None, init_channel=None, **kwargs):
        super().__init__(parent=parent, init_channel=init_channel, **kwargs)
        self._show_symbols = True
        
        # Create overlay widget
        self._overlay = SymbolOverlay(self)
        self._overlay.setGeometry(self.rect())
        self._overlay.raise_()  # Bring to front
        self._overlay.show()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_overlay'):
            self._overlay.setGeometry(self.rect())
            self._overlay.raise_()
    
    def update_indicators(self):
        """Override to update symbol display"""
        super().update_indicators()
        if hasattr(self, '_overlay'):
            self._overlay.update()

    # Explicitly expose onColor property (inherited from parent)
    @Property(QColor)
    def onColor(self):
        """Color for bits that are ON"""
        return self._on_color

    @onColor.setter
    def onColor(self, new_color):
        if self._on_color != new_color:
            self._on_color = new_color
            self.update_indicators()

    @Property(QColor)
    def offColor(self):
        """Color for bits that are OFF"""
        return self._off_color

    @offColor.setter
    def offColor(self, new_color):
        if self._off_color != new_color:
            self._off_color = new_color
            self.update_indicators()

    @Property(bool)
    def showSymbols(self):
        """Whether to show checkmark/X symbols inside circles"""
        return self._show_symbols

    @showSymbols.setter
    def showSymbols(self, value):
        if self._show_symbols != value:
            self._show_symbols = value
            if hasattr(self, '_overlay'):
                self._overlay._show_symbols = value
                self._overlay.update()

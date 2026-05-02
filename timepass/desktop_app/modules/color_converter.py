"""
Color Converter Module - Convert between color formats and generate palettes
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QLineEdit,
    QSlider, QSpinBox, QColorDialog, QScrollArea,
    QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
import colorsys
import random


class ColorPreview(QFrame):
    """Color preview widget"""
    
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 2px solid #374151;
            }
        """)
    
    def set_color(self, color: QColor):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color.name()};
                border-radius: 12px;
                border: 2px solid #374151;
            }}
        """)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class ColorSlider(QWidget):
    """Color component slider"""
    
    valueChanged = pyqtSignal(int)
    
    def __init__(self, label: str, max_val: int = 255, color: str = "#6366f1", parent=None):
        super().__init__(parent)
        self.max_val = max_val
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        self.label = QLabel(label)
        self.label.setFixedWidth(30)
        self.label.setStyleSheet("color: #9ca3af;")
        layout.addWidget(self.label)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, max_val)
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: #374151;
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {color};
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::sub-page:horizontal {{
                background: {color};
                border-radius: 4px;
            }}
        """)
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider, 1)
        
        self.spinbox = QSpinBox()
        self.spinbox.setRange(0, max_val)
        self.spinbox.setFixedWidth(60)
        self.spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 4px;
                color: #e5e7eb;
            }
        """)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)
        layout.addWidget(self.spinbox)
    
    def _on_value_changed(self, value: int):
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(value)
        self.spinbox.blockSignals(False)
        self.valueChanged.emit(value)
    
    def _on_spinbox_changed(self, value: int):
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        self.valueChanged.emit(value)
    
    def setValue(self, value: int):
        self.slider.blockSignals(True)
        self.spinbox.blockSignals(True)
        self.slider.setValue(value)
        self.spinbox.setValue(value)
        self.slider.blockSignals(False)
        self.spinbox.blockSignals(False)
    
    def value(self) -> int:
        return self.slider.value()


class PaletteColor(QFrame):
    """Single color in palette"""
    
    clicked = pyqtSignal(str)
    
    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(60, 60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                border: 2px solid transparent;
            }}
            QFrame:hover {{
                border: 2px solid #ffffff;
            }}
        """)
        self.setToolTip(color)
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.color)
        super().mousePressEvent(event)


class ColorConverterModule(QWidget):
    """Color Converter Module"""
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        self._current_color = QColor(100, 100, 255)
        self._updating = False
        self._setup_ui()
        self._update_from_color(self._current_color)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🎨 Color Converter")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f9fafb;
            }
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Random color button
        random_btn = QPushButton("🎲 Random")
        random_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: #818cf8;
            }
        """)
        random_btn.clicked.connect(self._random_color)
        header_layout.addWidget(random_btn)
        
        # Color picker button
        picker_btn = QPushButton("🎯 Pick Color")
        picker_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        picker_btn.clicked.connect(self._open_picker)
        header_layout.addWidget(picker_btn)
        
        layout.addLayout(header_layout)
        
        # Main content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)
        
        # Left side - Color preview and sliders
        self.left_frame = QFrame(self)
        self.left_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        left_layout = QVBoxLayout(self.left_frame)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(16)
        
        # Color preview
        preview_layout = QHBoxLayout()
        preview_layout.addStretch()
        
        self.color_preview = ColorPreview()
        self.color_preview.clicked.connect(self._open_picker)
        preview_layout.addWidget(self.color_preview)
        
        preview_layout.addStretch()
        left_layout.addLayout(preview_layout)
        
        # RGB Sliders
        rgb_label = QLabel("RGB")
        rgb_label.setStyleSheet("color: #f9fafb; font-weight: bold; font-size: 14px;")
        left_layout.addWidget(rgb_label)
        
        self.r_slider = ColorSlider("R", 255, "#ef4444")
        self.r_slider.valueChanged.connect(self._on_rgb_changed)
        left_layout.addWidget(self.r_slider)
        
        self.g_slider = ColorSlider("G", 255, "#22c55e")
        self.g_slider.valueChanged.connect(self._on_rgb_changed)
        left_layout.addWidget(self.g_slider)
        
        self.b_slider = ColorSlider("B", 255, "#3b82f6")
        self.b_slider.valueChanged.connect(self._on_rgb_changed)
        left_layout.addWidget(self.b_slider)
        
        # HSL Sliders
        hsl_label = QLabel("HSL")
        hsl_label.setStyleSheet("color: #f9fafb; font-weight: bold; font-size: 14px; margin-top: 8px;")
        left_layout.addWidget(hsl_label)
        
        self.h_slider = ColorSlider("H", 360, "#f59e0b")
        self.h_slider.valueChanged.connect(self._on_hsl_changed)
        left_layout.addWidget(self.h_slider)
        
        self.s_slider = ColorSlider("S", 100, "#8b5cf6")
        self.s_slider.valueChanged.connect(self._on_hsl_changed)
        left_layout.addWidget(self.s_slider)
        
        self.l_slider = ColorSlider("L", 100, "#06b6d4")
        self.l_slider.valueChanged.connect(self._on_hsl_changed)
        left_layout.addWidget(self.l_slider)
        
        left_layout.addStretch()
        content_layout.addWidget(self.left_frame, 1)
        
        # Right side - Color values and palettes
        self.right_frame = QFrame(self)
        self.right_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        right_layout = QVBoxLayout(self.right_frame)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(12)
        
        # Color values
        values_label = QLabel("Color Values")
        values_label.setStyleSheet("color: #f9fafb; font-weight: bold; font-size: 14px;")
        right_layout.addWidget(values_label)
        
        # Store containers as instance variables to prevent garbage collection
        self._value_containers = []
        
        # HEX
        self.hex_container, self.hex_input = self._create_value_row("HEX", "#6464FF")
        self.hex_input.textChanged.connect(self._on_hex_changed)
        right_layout.addWidget(self.hex_container)
        self._value_containers.append(self.hex_container)
        
        # RGB
        self.rgb_container, self.rgb_input = self._create_value_row("RGB", "rgb(100, 100, 255)")
        self.rgb_input.setReadOnly(True)
        right_layout.addWidget(self.rgb_container)
        self._value_containers.append(self.rgb_container)
        
        # HSL
        self.hsl_container, self.hsl_input = self._create_value_row("HSL", "hsl(240, 100%, 70%)")
        self.hsl_input.setReadOnly(True)
        right_layout.addWidget(self.hsl_container)
        self._value_containers.append(self.hsl_container)
        
        # RGBA
        self.rgba_container, self.rgba_input = self._create_value_row("RGBA", "rgba(100, 100, 255, 1)")
        self.rgba_input.setReadOnly(True)
        right_layout.addWidget(self.rgba_container)
        self._value_containers.append(self.rgba_container)
        
        # HSLA
        self.hsla_container, self.hsla_input = self._create_value_row("HSLA", "hsla(240, 100%, 70%, 1)")
        self.hsla_input.setReadOnly(True)
        right_layout.addWidget(self.hsla_container)
        self._value_containers.append(self.hsla_container)
        
        # Palette generators
        palette_label = QLabel("Generate Palette")
        palette_label.setStyleSheet("color: #f9fafb; font-weight: bold; font-size: 14px; margin-top: 12px;")
        right_layout.addWidget(palette_label)
        
        palette_btns = QHBoxLayout()
        
        comp_btn = QPushButton("Complementary")
        comp_btn.setStyleSheet(self._button_style())
        comp_btn.clicked.connect(lambda: self._generate_palette("complementary"))
        palette_btns.addWidget(comp_btn)
        
        analog_btn = QPushButton("Analogous")
        analog_btn.setStyleSheet(self._button_style())
        analog_btn.clicked.connect(lambda: self._generate_palette("analogous"))
        palette_btns.addWidget(analog_btn)
        
        triad_btn = QPushButton("Triadic")
        triad_btn.setStyleSheet(self._button_style())
        triad_btn.clicked.connect(lambda: self._generate_palette("triadic"))
        palette_btns.addWidget(triad_btn)
        
        right_layout.addLayout(palette_btns)
        
        palette_btns2 = QHBoxLayout()
        
        split_btn = QPushButton("Split Comp")
        split_btn.setStyleSheet(self._button_style())
        split_btn.clicked.connect(lambda: self._generate_palette("split"))
        palette_btns2.addWidget(split_btn)
        
        tetra_btn = QPushButton("Tetradic")
        tetra_btn.setStyleSheet(self._button_style())
        tetra_btn.clicked.connect(lambda: self._generate_palette("tetradic"))
        palette_btns2.addWidget(tetra_btn)
        
        mono_btn = QPushButton("Monochrome")
        mono_btn.setStyleSheet(self._button_style())
        mono_btn.clicked.connect(lambda: self._generate_palette("monochrome"))
        palette_btns2.addWidget(mono_btn)
        
        right_layout.addLayout(palette_btns2)
        
        # Palette display
        self.palette_container = QFrame(self)
        self.palette_container.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border-radius: 8px;
                border: 1px solid #374151;
            }
        """)
        self.palette_layout = QHBoxLayout(self.palette_container)
        self.palette_layout.setContentsMargins(12, 12, 12, 12)
        self.palette_layout.setSpacing(8)
        
        right_layout.addWidget(self.palette_container)
        
        right_layout.addStretch()
        content_layout.addWidget(self.right_frame, 1)
        
        layout.addLayout(content_layout, 1)
        
        # Saved colors
        self.saved_frame = QFrame(self)
        self.saved_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 8px;
                border: 1px solid #374151;
            }
        """)
        saved_layout = QVBoxLayout(self.saved_frame)
        saved_layout.setContentsMargins(16, 12, 16, 12)
        
        saved_header = QHBoxLayout()
        saved_label = QLabel("💾 Saved Colors")
        saved_label.setStyleSheet("color: #f9fafb; font-weight: bold;")
        saved_header.addWidget(saved_label)
        saved_header.addStretch()
        
        save_btn = QPushButton("+ Save Current")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                color: white;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        save_btn.clicked.connect(self._save_color)
        saved_header.addWidget(save_btn)
        
        saved_layout.addLayout(saved_header)
        
        # Saved colors scroll area
        self.saved_colors_widget = QWidget()
        self.saved_colors_layout = QHBoxLayout(self.saved_colors_widget)
        self.saved_colors_layout.setContentsMargins(0, 8, 0, 0)
        self.saved_colors_layout.setSpacing(8)
        self.saved_colors_layout.addStretch()
        
        saved_layout.addWidget(self.saved_colors_widget)
        
        layout.addWidget(self.saved_frame)
        
        # Load saved colors
        self._load_saved_colors()
    
    def _create_value_row(self, label: str, placeholder: str):
        """Create a labeled input row. Returns (container, input_field) tuple."""
        container = QWidget(self)  # Set parent to prevent garbage collection
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        lbl = QLabel(label, container)
        lbl.setFixedWidth(50)
        lbl.setStyleSheet("color: #9ca3af;")
        layout.addWidget(lbl)
        
        input_field = QLineEdit(container)
        input_field.setPlaceholderText(placeholder)
        input_field.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
                font-family: 'Consolas', monospace;
            }
        """)
        layout.addWidget(input_field, 1)
        
        copy_btn = QPushButton("📋", container)
        copy_btn.setFixedSize(32, 32)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #4b5563;
                border-radius: 4px;
                color: #9ca3af;
            }
            QPushButton:hover {
                background-color: #374151;
            }
        """)
        copy_btn.clicked.connect(lambda: self._copy_value(input_field))
        layout.addWidget(copy_btn)
        
        return container, input_field
    
    def _button_style(self) -> str:
        return """
            QPushButton {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px 12px;
                color: #e5e7eb;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """
    
    def _on_rgb_changed(self):
        if self._updating:
            return
        
        r = self.r_slider.value()
        g = self.g_slider.value()
        b = self.b_slider.value()
        
        self._current_color = QColor(r, g, b)
        self._update_from_color(self._current_color)
    
    def _on_hsl_changed(self):
        if self._updating:
            return
        
        h = self.h_slider.value() / 360.0
        s = self.s_slider.value() / 100.0
        l = self.l_slider.value() / 100.0
        
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        self._current_color = QColor(int(r * 255), int(g * 255), int(b * 255))
        self._update_from_color(self._current_color, update_hsl=False)
    
    def _on_hex_changed(self):
        if self._updating:
            return
        
        hex_value = self.hex_input.text().strip()
        if not hex_value.startswith('#'):
            hex_value = '#' + hex_value
        
        color = QColor(hex_value)
        if color.isValid():
            self._current_color = color
            self._update_from_color(color, update_hex=False)
    
    def _update_from_color(self, color: QColor, update_rgb=True, update_hsl=True, update_hex=True):
        """Update all UI from color"""
        self._updating = True
        
        # Update preview
        self.color_preview.set_color(color)
        
        r, g, b = color.red(), color.green(), color.blue()
        
        # Update RGB sliders
        if update_rgb:
            self.r_slider.setValue(r)
            self.g_slider.setValue(g)
            self.b_slider.setValue(b)
        
        # Update HSL sliders
        if update_hsl:
            h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
            self.h_slider.setValue(int(h * 360))
            self.s_slider.setValue(int(s * 100))
            self.l_slider.setValue(int(l * 100))
        
        # Update text values
        if update_hex:
            self.hex_input.setText(color.name().upper())
        
        self.rgb_input.setText(f"rgb({r}, {g}, {b})")
        
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        self.hsl_input.setText(f"hsl({int(h*360)}, {int(s*100)}%, {int(l*100)}%)")
        self.rgba_input.setText(f"rgba({r}, {g}, {b}, 1)")
        self.hsla_input.setText(f"hsla({int(h*360)}, {int(s*100)}%, {int(l*100)}%, 1)")
        
        self._updating = False
    
    def _random_color(self):
        """Generate random color"""
        color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self._current_color = color
        self._update_from_color(color)
    
    def _open_picker(self):
        """Open system color picker"""
        color = QColorDialog.getColor(self._current_color, self, "Pick Color")
        if color.isValid():
            self._current_color = color
            self._update_from_color(color)
    
    def _generate_palette(self, palette_type: str):
        """Generate color palette"""
        # Clear existing
        while self.palette_layout.count() > 0:
            item = self.palette_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        r, g, b = self._current_color.red()/255, self._current_color.green()/255, self._current_color.blue()/255
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        
        colors = []
        
        if palette_type == "complementary":
            colors = [
                self._hls_to_hex(h, l, s),
                self._hls_to_hex((h + 0.5) % 1, l, s),
            ]
        elif palette_type == "analogous":
            colors = [
                self._hls_to_hex((h - 0.083) % 1, l, s),
                self._hls_to_hex(h, l, s),
                self._hls_to_hex((h + 0.083) % 1, l, s),
            ]
        elif palette_type == "triadic":
            colors = [
                self._hls_to_hex(h, l, s),
                self._hls_to_hex((h + 0.333) % 1, l, s),
                self._hls_to_hex((h + 0.666) % 1, l, s),
            ]
        elif palette_type == "split":
            colors = [
                self._hls_to_hex(h, l, s),
                self._hls_to_hex((h + 0.417) % 1, l, s),
                self._hls_to_hex((h + 0.583) % 1, l, s),
            ]
        elif palette_type == "tetradic":
            colors = [
                self._hls_to_hex(h, l, s),
                self._hls_to_hex((h + 0.25) % 1, l, s),
                self._hls_to_hex((h + 0.5) % 1, l, s),
                self._hls_to_hex((h + 0.75) % 1, l, s),
            ]
        elif palette_type == "monochrome":
            colors = [
                self._hls_to_hex(h, max(0, l - 0.3), s),
                self._hls_to_hex(h, max(0, l - 0.15), s),
                self._hls_to_hex(h, l, s),
                self._hls_to_hex(h, min(1, l + 0.15), s),
                self._hls_to_hex(h, min(1, l + 0.3), s),
            ]
        
        # Add color widgets
        for color_hex in colors:
            color_widget = PaletteColor(color_hex)
            color_widget.clicked.connect(self._load_palette_color)
            self.palette_layout.addWidget(color_widget)
        
        self.palette_layout.addStretch()
    
    def _hls_to_hex(self, h: float, l: float, s: float) -> str:
        """Convert HLS to hex"""
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    
    def _load_palette_color(self, color_hex: str):
        """Load color from palette"""
        color = QColor(color_hex)
        self._current_color = color
        self._update_from_color(color)
    
    def _save_color(self):
        """Save current color"""
        from core.database import get_session, SavedColor
        
        with get_session() as session:
            saved = SavedColor(
                hex_value=self._current_color.name(),
                name=f"Color {self._current_color.name()}"
            )
            session.add(saved)
            session.commit()
        
        self._load_saved_colors()
    
    def _load_saved_colors(self):
        """Load saved colors from database"""
        # Clear existing
        while self.saved_colors_layout.count() > 1:
            item = self.saved_colors_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        from core.database import get_session, SavedColor
        
        with get_session() as session:
            colors = session.query(SavedColor).order_by(SavedColor.created_at.desc()).limit(20).all()
            
            for color in colors:
                color_widget = PaletteColor(color.hex_value)
                color_widget.clicked.connect(self._load_palette_color)
                self.saved_colors_layout.insertWidget(self.saved_colors_layout.count() - 1, color_widget)
    
    def _copy_value(self, input_field: QLineEdit):
        """Copy value to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(input_field.text())

"""
QR Code Generator Module - Generate and scan QR codes
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QPlainTextEdit,
    QComboBox, QTabWidget, QLineEdit, QSpinBox,
    QColorDialog, QFileDialog, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, QBuffer, QIODevice
from PyQt6.QtGui import QPixmap, QImage, QColor
import io
import os

try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False


class QRCodeGeneratorModule(QWidget):
    """QR Code Generator Module"""
    
    ERROR_LEVELS = {
        "Low (7%)": ERROR_CORRECT_L if HAS_QRCODE else 0,
        "Medium (15%)": ERROR_CORRECT_M if HAS_QRCODE else 1,
        "Quartile (25%)": ERROR_CORRECT_Q if HAS_QRCODE else 2,
        "High (30%)": ERROR_CORRECT_H if HAS_QRCODE else 3,
    }
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        self._qr_image = None
        self._fg_color = QColor("#000000")
        self._bg_color = QColor("#ffffff")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        title = QLabel("📱 QR Code Generator")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f9fafb;
            }
        """)
        layout.addWidget(title)
        
        if not HAS_QRCODE:
            error_label = QLabel("⚠️ qrcode library not installed. Run: pip install qrcode[pil]")
            error_label.setStyleSheet("color: #f59e0b; padding: 20px;")
            layout.addWidget(error_label)
            layout.addStretch()
            return
        
        # Main content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)
        
        # Left - Input
        self.input_frame = QFrame(self)
        self.input_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        input_layout = QVBoxLayout(self.input_frame)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(16)
        
        # Content type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Text/URL", "Email", "Phone", "SMS", "WiFi", "vCard"])
        self.type_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 8px 16px;
                color: #e5e7eb;
                min-width: 120px;
            }
        """)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        
        input_layout.addLayout(type_layout)
        
        # Content input (stacked widget would be better, but keeping it simple)
        self.content_input = QPlainTextEdit()
        self.content_input.setPlaceholderText("Enter text or URL to encode...")
        self.content_input.setStyleSheet("""
            QPlainTextEdit {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
                color: #e5e7eb;
                font-family: 'Consolas', monospace;
                font-size: 13px;
            }
        """)
        self.content_input.textChanged.connect(self._on_content_changed)
        input_layout.addWidget(self.content_input)
        
        # Options
        options_label = QLabel("Options")
        options_label.setStyleSheet("color: #f9fafb; font-weight: bold;")
        input_layout.addWidget(options_label)
        
        options_grid = QGridLayout()
        options_grid.setSpacing(12)
        
        # Size
        options_grid.addWidget(QLabel("Size:"), 0, 0)
        self.size_spin = QSpinBox()
        self.size_spin.setRange(100, 1000)
        self.size_spin.setValue(300)
        self.size_spin.setSuffix(" px")
        self.size_spin.setStyleSheet("""
            QSpinBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px;
                color: #e5e7eb;
            }
        """)
        options_grid.addWidget(self.size_spin, 0, 1)
        
        # Error correction
        options_grid.addWidget(QLabel("Error Correction:"), 0, 2)
        self.error_combo = QComboBox()
        self.error_combo.addItems(list(self.ERROR_LEVELS.keys()))
        self.error_combo.setCurrentIndex(1)
        self.error_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px 12px;
                color: #e5e7eb;
            }
        """)
        options_grid.addWidget(self.error_combo, 0, 3)
        
        # Colors
        options_grid.addWidget(QLabel("Foreground:"), 1, 0)
        self.fg_btn = QPushButton()
        self.fg_btn.setFixedSize(60, 30)
        self.fg_btn.setStyleSheet(f"background-color: {self._fg_color.name()}; border-radius: 4px;")
        self.fg_btn.clicked.connect(self._pick_fg_color)
        options_grid.addWidget(self.fg_btn, 1, 1)
        
        options_grid.addWidget(QLabel("Background:"), 1, 2)
        self.bg_btn = QPushButton()
        self.bg_btn.setFixedSize(60, 30)
        self.bg_btn.setStyleSheet(f"background-color: {self._bg_color.name()}; border-radius: 4px;")
        self.bg_btn.clicked.connect(self._pick_bg_color)
        options_grid.addWidget(self.bg_btn, 1, 3)
        
        input_layout.addLayout(options_grid)
        
        # Generate button
        generate_btn = QPushButton("🔄 Generate QR Code")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                border: none;
                border-radius: 8px;
                padding: 14px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #818cf8;
            }
        """)
        generate_btn.clicked.connect(self._generate_qr)
        input_layout.addWidget(generate_btn)
        
        content_layout.addWidget(self.input_frame, 1)
        
        # Right - Preview
        self.preview_frame = QFrame(self)
        self.preview_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(20, 20, 20, 20)
        preview_layout.setSpacing(16)
        
        preview_label = QLabel("Preview")
        preview_label.setStyleSheet("color: #f9fafb; font-weight: bold;")
        preview_layout.addWidget(preview_label)
        
        # QR display
        self.qr_display = QLabel()
        self.qr_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_display.setMinimumSize(300, 300)
        self.qr_display.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border-radius: 8px;
            }
        """)
        preview_layout.addWidget(self.qr_display, 1)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        copy_btn = QPushButton("📋 Copy")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        copy_btn.clicked.connect(self._copy_qr)
        action_layout.addWidget(copy_btn)
        
        save_btn = QPushButton("💾 Save")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #818cf8;
            }
        """)
        save_btn.clicked.connect(self._save_qr)
        action_layout.addWidget(save_btn)
        
        preview_layout.addLayout(action_layout)
        
        content_layout.addWidget(self.preview_frame, 1)
        
        layout.addLayout(content_layout, 1)
        
        # Templates section
        self.templates_frame = QFrame(self)
        self.templates_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 8px;
                border: 1px solid #374151;
            }
        """)
        templates_layout = QVBoxLayout(self.templates_frame)
        templates_layout.setContentsMargins(16, 12, 16, 12)
        
        templates_header = QLabel("📚 Quick Templates")
        templates_header.setStyleSheet("color: #f9fafb; font-weight: bold;")
        templates_layout.addWidget(templates_header)
        
        templates_btn_layout = QHBoxLayout()
        
        url_btn = QPushButton("🌐 URL")
        url_btn.setStyleSheet(self._template_btn_style())
        url_btn.clicked.connect(lambda: self._set_template("url"))
        templates_btn_layout.addWidget(url_btn)
        
        email_btn = QPushButton("📧 Email")
        email_btn.setStyleSheet(self._template_btn_style())
        email_btn.clicked.connect(lambda: self._set_template("email"))
        templates_btn_layout.addWidget(email_btn)
        
        phone_btn = QPushButton("📞 Phone")
        phone_btn.setStyleSheet(self._template_btn_style())
        phone_btn.clicked.connect(lambda: self._set_template("phone"))
        templates_btn_layout.addWidget(phone_btn)
        
        wifi_btn = QPushButton("📶 WiFi")
        wifi_btn.setStyleSheet(self._template_btn_style())
        wifi_btn.clicked.connect(lambda: self._set_template("wifi"))
        templates_btn_layout.addWidget(wifi_btn)
        
        vcard_btn = QPushButton("👤 vCard")
        vcard_btn.setStyleSheet(self._template_btn_style())
        vcard_btn.clicked.connect(lambda: self._set_template("vcard"))
        templates_btn_layout.addWidget(vcard_btn)
        
        templates_btn_layout.addStretch()
        templates_layout.addLayout(templates_btn_layout)
        
        layout.addWidget(self.templates_frame)
    
    def _template_btn_style(self) -> str:
        return """
            QPushButton {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px 16px;
                color: #e5e7eb;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """
    
    def _on_type_changed(self, type_name: str):
        """Update placeholder based on content type"""
        placeholders = {
            "Text/URL": "Enter text or URL to encode...",
            "Email": "mailto:email@example.com?subject=Hello",
            "Phone": "tel:+1234567890",
            "SMS": "smsto:+1234567890:Your message here",
            "WiFi": "WIFI:T:WPA;S:NetworkName;P:Password;;",
            "vCard": "BEGIN:VCARD\nVERSION:3.0\nN:Doe;John\nTEL:+1234567890\nEMAIL:john@example.com\nEND:VCARD"
        }
        self.content_input.setPlaceholderText(placeholders.get(type_name, ""))
    
    def _on_content_changed(self):
        """Auto-generate on content change (with debounce in production)"""
        pass  # Could add auto-generation here
    
    def _pick_fg_color(self):
        """Pick foreground color"""
        color = QColorDialog.getColor(self._fg_color, self, "Foreground Color")
        if color.isValid():
            self._fg_color = color
            self.fg_btn.setStyleSheet(f"background-color: {color.name()}; border-radius: 4px;")
    
    def _pick_bg_color(self):
        """Pick background color"""
        color = QColorDialog.getColor(self._bg_color, self, "Background Color")
        if color.isValid():
            self._bg_color = color
            self.bg_btn.setStyleSheet(f"background-color: {color.name()}; border-radius: 4px;")
    
    def _generate_qr(self):
        """Generate QR code"""
        content = self.content_input.toPlainText().strip()
        if not content:
            return
        
        try:
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=self.ERROR_LEVELS[self.error_combo.currentText()],
                box_size=10,
                border=4
            )
            qr.add_data(content)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(
                fill_color=self._fg_color.name(),
                back_color=self._bg_color.name()
            )
            
            # Convert to QPixmap
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            qimage = QImage()
            qimage.loadFromData(buffer.getvalue())
            
            # Scale to display size
            size = self.size_spin.value()
            pixmap = QPixmap.fromImage(qimage).scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.qr_display.setPixmap(pixmap)
            self._qr_image = img
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate QR code: {e}")
    
    def _copy_qr(self):
        """Copy QR code to clipboard"""
        if not self._qr_image:
            return
        
        try:
            # Convert PIL image to QPixmap
            buffer = io.BytesIO()
            self._qr_image.save(buffer, format='PNG')
            buffer.seek(0)
            
            qimage = QImage()
            qimage.loadFromData(buffer.getvalue())
            pixmap = QPixmap.fromImage(qimage)
            
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(pixmap)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to copy: {e}")
    
    def _save_qr(self):
        """Save QR code to file"""
        if not self._qr_image:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save QR Code",
            "qrcode.png",
            "PNG Images (*.png);;JPEG Images (*.jpg);;All Files (*)"
        )
        
        if file_path:
            try:
                # Resize to specified size
                size = self.size_spin.value()
                resized = self._qr_image.resize((size, size))
                resized.save(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save: {e}")
    
    def _set_template(self, template_type: str):
        """Set content template"""
        templates = {
            "url": "https://example.com",
            "email": "mailto:your@email.com?subject=Hello&body=Message%20here",
            "phone": "tel:+1234567890",
            "wifi": "WIFI:T:WPA;S:YourNetworkName;P:YourPassword;;",
            "vcard": """BEGIN:VCARD
VERSION:3.0
N:Doe;John
FN:John Doe
TEL;TYPE=CELL:+1234567890
EMAIL:john@example.com
ORG:Company Name
TITLE:Job Title
END:VCARD"""
        }
        
        if template_type in templates:
            self.content_input.setPlainText(templates[template_type])
            
            # Update type combo
            type_map = {
                "url": "Text/URL",
                "email": "Email",
                "phone": "Phone",
                "wifi": "WiFi",
                "vcard": "vCard"
            }
            if template_type in type_map:
                self.type_combo.setCurrentText(type_map[template_type])

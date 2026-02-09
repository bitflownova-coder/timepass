"""
Encoder/Decoder Module - Encode and decode various formats
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QPlainTextEdit,
    QComboBox, QTabWidget, QLineEdit, QMessageBox,
    QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import base64
import urllib.parse
import hashlib
import hmac
import json
from typing import Optional


class EncoderDecoderModule(QWidget):
    """Encoder/Decoder Module"""
    
    ENCODINGS = [
        "Base64",
        "Base64 URL Safe",
        "URL Encode",
        "HTML Entities",
        "Unicode Escape",
        "Hex",
        "Binary",
        "ROT13",
    ]
    
    HASHES = [
        "MD5",
        "SHA-1",
        "SHA-256",
        "SHA-384",
        "SHA-512",
        "HMAC-SHA256",
    ]
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        title = QLabel("🔐 Encoder / Decoder")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f9fafb;
            }
        """)
        layout.addWidget(title)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #374151;
                border-radius: 8px;
                background-color: #1f2937;
            }
            QTabBar::tab {
                background-color: #374151;
                color: #9ca3af;
                border: 1px solid #4b5563;
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #1f2937;
                color: #f9fafb;
                border-bottom-color: #1f2937;
            }
            QTabBar::tab:hover {
                background-color: #4b5563;
            }
        """)
        
        # Encoding tab
        tabs.addTab(self._create_encoding_tab(), "🔄 Encoding")
        
        # Hashing tab
        tabs.addTab(self._create_hashing_tab(), "🔒 Hashing")
        
        # JWT tab
        tabs.addTab(self._create_jwt_tab(), "🎫 JWT")
        
        layout.addWidget(tabs, 1)
    
    def _create_encoding_tab(self) -> QWidget:
        """Create encoding/decoding tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Encoding selector
        selector_layout = QHBoxLayout()
        
        selector_layout.addWidget(QLabel("Encoding:"))
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(self.ENCODINGS)
        self.encoding_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 8px 16px;
                color: #e5e7eb;
                min-width: 150px;
            }
        """)
        selector_layout.addWidget(self.encoding_combo)
        selector_layout.addStretch()
        
        # Action buttons
        encode_btn = QPushButton("⬇️ Encode")
        encode_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        encode_btn.clicked.connect(self._encode)
        selector_layout.addWidget(encode_btn)
        
        decode_btn = QPushButton("⬆️ Decode")
        decode_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #818cf8;
            }
        """)
        decode_btn.clicked.connect(self._decode)
        selector_layout.addWidget(decode_btn)
        
        layout.addLayout(selector_layout)
        
        # Input/Output splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Input
        input_frame = self._create_text_frame("Input", True)
        self.enc_input = input_frame.findChild(QPlainTextEdit)
        splitter.addWidget(input_frame)
        
        # Output
        output_frame = self._create_text_frame("Output", False)
        self.enc_output = output_frame.findChild(QPlainTextEdit)
        splitter.addWidget(output_frame)
        
        splitter.setSizes([300, 300])
        layout.addWidget(splitter, 1)
        
        return widget
    
    def _create_hashing_tab(self) -> QWidget:
        """Create hashing tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Hash selector
        selector_layout = QHBoxLayout()
        
        selector_layout.addWidget(QLabel("Algorithm:"))
        self.hash_combo = QComboBox()
        self.hash_combo.addItems(self.HASHES)
        self.hash_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 8px 16px;
                color: #e5e7eb;
                min-width: 150px;
            }
        """)
        self.hash_combo.currentTextChanged.connect(self._on_hash_changed)
        selector_layout.addWidget(self.hash_combo)
        
        # HMAC key (hidden by default)
        self.hmac_label = QLabel("Secret Key:")
        self.hmac_label.setVisible(False)
        selector_layout.addWidget(self.hmac_label)
        
        self.hmac_key = QLineEdit()
        self.hmac_key.setPlaceholderText("Enter HMAC secret key...")
        self.hmac_key.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
            }
        """)
        self.hmac_key.setVisible(False)
        selector_layout.addWidget(self.hmac_key)
        
        selector_layout.addStretch()
        
        hash_btn = QPushButton("🔒 Generate Hash")
        hash_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #d97706;
            }
        """)
        hash_btn.clicked.connect(self._generate_hash)
        selector_layout.addWidget(hash_btn)
        
        layout.addLayout(selector_layout)
        
        # Input
        input_frame = self._create_text_frame("Input", True)
        self.hash_input = input_frame.findChild(QPlainTextEdit)
        layout.addWidget(input_frame, 1)
        
        # Output (single line)
        self.hash_output_frame = QFrame(self)
        self.hash_output_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
            }
        """)
        output_layout = QVBoxLayout(self.hash_output_frame)
        output_layout.setContentsMargins(12, 12, 12, 12)
        
        output_header = QHBoxLayout()
        output_header.addWidget(QLabel("Hash Output:"))
        output_header.addStretch()
        
        copy_btn = QPushButton("📋 Copy")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 4px 12px;
                color: #9ca3af;
            }
            QPushButton:hover {
                background-color: #374151;
            }
        """)
        copy_btn.clicked.connect(lambda: self._copy_text(self.hash_output))
        output_header.addWidget(copy_btn)
        output_layout.addLayout(output_header)
        
        self.hash_output = QLineEdit()
        self.hash_output.setReadOnly(True)
        self.hash_output.setStyleSheet("""
            QLineEdit {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 4px;
                padding: 12px;
                color: #10b981;
                font-family: 'Consolas', monospace;
                font-size: 14px;
            }
        """)
        output_layout.addWidget(self.hash_output)
        
        layout.addWidget(self.hash_output_frame)
        
        return widget
    
    def _create_jwt_tab(self) -> QWidget:
        """Create JWT decode tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # JWT input
        input_layout = QVBoxLayout()
        
        input_header = QHBoxLayout()
        input_header.addWidget(QLabel("JWT Token:"))
        input_header.addStretch()
        
        decode_btn = QPushButton("🔍 Decode JWT")
        decode_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }
        """)
        decode_btn.clicked.connect(self._decode_jwt)
        input_header.addWidget(decode_btn)
        
        input_layout.addLayout(input_header)
        
        self.jwt_input = QPlainTextEdit()
        self.jwt_input.setPlaceholderText("Paste your JWT token here...")
        self.jwt_input.setMaximumHeight(100)
        self.jwt_input.setStyleSheet("""
            QPlainTextEdit {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
                color: #e5e7eb;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        input_layout.addWidget(self.jwt_input)
        
        layout.addLayout(input_layout)
        
        # JWT parts display
        parts_layout = QHBoxLayout()
        
        # Header
        self.jwt_header_frame = QFrame(self)
        self.jwt_header_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 2px solid #ef4444;
                border-radius: 8px;
            }
        """)
        header_layout = QVBoxLayout(self.jwt_header_frame)
        header_layout.setContentsMargins(12, 12, 12, 12)
        
        header_label = QLabel("🔴 Header")
        header_label.setStyleSheet("color: #ef4444; font-weight: bold;")
        header_layout.addWidget(header_label)
        
        self.jwt_header = QPlainTextEdit()
        self.jwt_header.setReadOnly(True)
        self.jwt_header.setStyleSheet("""
            QPlainTextEdit {
                background-color: transparent;
                border: none;
                color: #fca5a5;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        header_layout.addWidget(self.jwt_header)
        
        parts_layout.addWidget(self.jwt_header_frame)
        
        # Payload
        self.jwt_payload_frame = QFrame(self)
        self.jwt_payload_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 2px solid #a855f7;
                border-radius: 8px;
            }
        """)
        payload_layout = QVBoxLayout(self.jwt_payload_frame)
        payload_layout.setContentsMargins(12, 12, 12, 12)
        
        payload_label = QLabel("🟣 Payload")
        payload_label.setStyleSheet("color: #a855f7; font-weight: bold;")
        payload_layout.addWidget(payload_label)
        
        self.jwt_payload = QPlainTextEdit()
        self.jwt_payload.setReadOnly(True)
        self.jwt_payload.setStyleSheet("""
            QPlainTextEdit {
                background-color: transparent;
                border: none;
                color: #d8b4fe;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        payload_layout.addWidget(self.jwt_payload)
        
        parts_layout.addWidget(self.jwt_payload_frame)
        
        # Signature
        self.jwt_sig_frame = QFrame(self)
        self.jwt_sig_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 2px solid #22d3ee;
                border-radius: 8px;
            }
        """)
        sig_layout = QVBoxLayout(self.jwt_sig_frame)
        sig_layout.setContentsMargins(12, 12, 12, 12)
        
        sig_label = QLabel("🔵 Signature")
        sig_label.setStyleSheet("color: #22d3ee; font-weight: bold;")
        sig_layout.addWidget(sig_label)
        
        self.jwt_signature = QPlainTextEdit()
        self.jwt_signature.setReadOnly(True)
        self.jwt_signature.setStyleSheet("""
            QPlainTextEdit {
                background-color: transparent;
                border: none;
                color: #67e8f9;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        sig_layout.addWidget(self.jwt_signature)
        
        parts_layout.addWidget(self.jwt_sig_frame)
        
        layout.addLayout(parts_layout, 1)
        
        # Status
        self.jwt_status = QLabel()
        self.jwt_status.setStyleSheet("color: #9ca3af;")
        layout.addWidget(self.jwt_status)
        
        return widget
    
    def _create_text_frame(self, label: str, is_input: bool) -> QFrame:
        """Create a text frame with header"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        
        header = QHBoxLayout()
        header.addWidget(QLabel(f"{label}:"))
        header.addStretch()
        
        if is_input:
            paste_btn = QPushButton("📋 Paste")
            paste_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid #4b5563;
                    border-radius: 4px;
                    padding: 4px 12px;
                    color: #9ca3af;
                }
                QPushButton:hover {
                    background-color: #374151;
                }
            """)
            paste_btn.clicked.connect(lambda: self._paste_to_input(frame))
            header.addWidget(paste_btn)
            
            clear_btn = QPushButton("🗑️ Clear")
            clear_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid #4b5563;
                    border-radius: 4px;
                    padding: 4px 12px;
                    color: #9ca3af;
                }
                QPushButton:hover {
                    background-color: #374151;
                }
            """)
            clear_btn.clicked.connect(lambda: frame.findChild(QPlainTextEdit).clear())
            header.addWidget(clear_btn)
        else:
            copy_btn = QPushButton("📋 Copy")
            copy_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid #4b5563;
                    border-radius: 4px;
                    padding: 4px 12px;
                    color: #9ca3af;
                }
                QPushButton:hover {
                    background-color: #374151;
                }
            """)
            copy_btn.clicked.connect(lambda: self._copy_output(frame))
            header.addWidget(copy_btn)
        
        layout.addLayout(header)
        
        text_edit = QPlainTextEdit()
        text_edit.setReadOnly(not is_input)
        text_edit.setPlaceholderText(f"Enter text to {'encode/decode' if is_input else 'see result'}...")
        text_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: transparent;
                border: none;
                color: #e5e7eb;
                font-family: 'Consolas', monospace;
                font-size: 13px;
            }
        """)
        layout.addWidget(text_edit)
        
        return frame
    
    def _encode(self):
        """Encode input text"""
        text = self.enc_input.toPlainText()
        encoding = self.encoding_combo.currentText()
        
        try:
            result = self._apply_encoding(text, encoding, encode=True)
            self.enc_output.setPlainText(result)
        except Exception as e:
            QMessageBox.warning(self, "Encoding Error", str(e))
    
    def _decode(self):
        """Decode input text"""
        text = self.enc_input.toPlainText()
        encoding = self.encoding_combo.currentText()
        
        try:
            result = self._apply_encoding(text, encoding, encode=False)
            self.enc_output.setPlainText(result)
        except Exception as e:
            QMessageBox.warning(self, "Decoding Error", str(e))
    
    def _apply_encoding(self, text: str, encoding: str, encode: bool) -> str:
        """Apply encoding or decoding"""
        if encoding == "Base64":
            if encode:
                return base64.b64encode(text.encode()).decode()
            else:
                return base64.b64decode(text.encode()).decode()
        
        elif encoding == "Base64 URL Safe":
            if encode:
                return base64.urlsafe_b64encode(text.encode()).decode()
            else:
                return base64.urlsafe_b64decode(text.encode()).decode()
        
        elif encoding == "URL Encode":
            if encode:
                return urllib.parse.quote(text, safe='')
            else:
                return urllib.parse.unquote(text)
        
        elif encoding == "HTML Entities":
            import html
            if encode:
                return html.escape(text)
            else:
                return html.unescape(text)
        
        elif encoding == "Unicode Escape":
            if encode:
                return text.encode('unicode_escape').decode()
            else:
                return text.encode().decode('unicode_escape')
        
        elif encoding == "Hex":
            if encode:
                return text.encode().hex()
            else:
                return bytes.fromhex(text).decode()
        
        elif encoding == "Binary":
            if encode:
                return ' '.join(format(ord(c), '08b') for c in text)
            else:
                binary_values = text.split()
                return ''.join(chr(int(b, 2)) for b in binary_values)
        
        elif encoding == "ROT13":
            import codecs
            return codecs.encode(text, 'rot_13')
        
        return text
    
    def _on_hash_changed(self, algorithm: str):
        """Handle hash algorithm change"""
        is_hmac = algorithm.startswith("HMAC")
        self.hmac_label.setVisible(is_hmac)
        self.hmac_key.setVisible(is_hmac)
    
    def _generate_hash(self):
        """Generate hash from input"""
        text = self.hash_input.toPlainText()
        algorithm = self.hash_combo.currentText()
        
        try:
            if algorithm == "MD5":
                result = hashlib.md5(text.encode()).hexdigest()
            elif algorithm == "SHA-1":
                result = hashlib.sha1(text.encode()).hexdigest()
            elif algorithm == "SHA-256":
                result = hashlib.sha256(text.encode()).hexdigest()
            elif algorithm == "SHA-384":
                result = hashlib.sha384(text.encode()).hexdigest()
            elif algorithm == "SHA-512":
                result = hashlib.sha512(text.encode()).hexdigest()
            elif algorithm == "HMAC-SHA256":
                key = self.hmac_key.text().encode()
                result = hmac.new(key, text.encode(), hashlib.sha256).hexdigest()
            else:
                result = ""
            
            self.hash_output.setText(result)
        except Exception as e:
            QMessageBox.warning(self, "Hash Error", str(e))
    
    def _decode_jwt(self):
        """Decode JWT token"""
        token = self.jwt_input.toPlainText().strip()
        
        if not token:
            return
        
        parts = token.split('.')
        if len(parts) != 3:
            self.jwt_status.setText("✗ Invalid JWT format (should have 3 parts)")
            self.jwt_status.setStyleSheet("color: #ef4444;")
            return
        
        try:
            # Decode header
            header_b64 = parts[0]
            # Add padding if needed
            header_b64 += '=' * (4 - len(header_b64) % 4) if len(header_b64) % 4 else ''
            header_json = base64.urlsafe_b64decode(header_b64).decode()
            header_data = json.loads(header_json)
            self.jwt_header.setPlainText(json.dumps(header_data, indent=2))
            
            # Decode payload
            payload_b64 = parts[1]
            payload_b64 += '=' * (4 - len(payload_b64) % 4) if len(payload_b64) % 4 else ''
            payload_json = base64.urlsafe_b64decode(payload_b64).decode()
            payload_data = json.loads(payload_json)
            self.jwt_payload.setPlainText(json.dumps(payload_data, indent=2))
            
            # Signature (just display base64)
            self.jwt_signature.setPlainText(parts[2])
            
            # Check expiration
            exp = payload_data.get('exp')
            if exp:
                import time
                if exp < time.time():
                    self.jwt_status.setText(f"⚠️ Token expired")
                    self.jwt_status.setStyleSheet("color: #f59e0b;")
                else:
                    from datetime import datetime
                    exp_date = datetime.fromtimestamp(exp)
                    self.jwt_status.setText(f"✓ Valid until {exp_date}")
                    self.jwt_status.setStyleSheet("color: #10b981;")
            else:
                self.jwt_status.setText("✓ Token decoded (no expiration)")
                self.jwt_status.setStyleSheet("color: #10b981;")
            
        except Exception as e:
            self.jwt_status.setText(f"✗ Decode error: {e}")
            self.jwt_status.setStyleSheet("color: #ef4444;")
    
    def _paste_to_input(self, frame: QFrame):
        """Paste clipboard to input"""
        from PyQt6.QtWidgets import QApplication
        text_edit = frame.findChild(QPlainTextEdit)
        if text_edit:
            clipboard = QApplication.clipboard()
            text_edit.setPlainText(clipboard.text())
    
    def _copy_output(self, frame: QFrame):
        """Copy output to clipboard"""
        from PyQt6.QtWidgets import QApplication
        text_edit = frame.findChild(QPlainTextEdit)
        if text_edit:
            clipboard = QApplication.clipboard()
            clipboard.setText(text_edit.toPlainText())
    
    def _copy_text(self, widget):
        """Copy text from widget to clipboard"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        if hasattr(widget, 'text'):
            clipboard.setText(widget.text())
        elif hasattr(widget, 'toPlainText'):
            clipboard.setText(widget.toPlainText())

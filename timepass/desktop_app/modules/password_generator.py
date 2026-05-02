"""
Password Generator Module - Generate secure passwords and passphrases
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QLineEdit,
    QSlider, QSpinBox, QCheckBox, QListWidget,
    QListWidgetItem, QApplication, QProgressBar,
    QTabWidget, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
import secrets
import string
import math
import hashlib
from datetime import datetime


class PasswordStrengthBar(QProgressBar):
    """Password strength indicator"""
    
    STRENGTH_COLORS = [
        (20, "#ef4444"),   # Very Weak
        (40, "#f97316"),   # Weak
        (60, "#f59e0b"),   # Fair
        (80, "#84cc16"),   # Strong
        (100, "#10b981"),  # Very Strong
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setFixedHeight(8)
        self._update_style(0)
    
    def setValue(self, value: int):
        super().setValue(value)
        self._update_style(value)
    
    def _update_style(self, value: int):
        color = "#374151"
        for threshold, c in self.STRENGTH_COLORS:
            if value <= threshold:
                color = c
                break
        
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: #374151;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)


class PasswordGeneratorModule(QWidget):
    """Password Generator Module"""
    
    WORD_LIST = [
        "apple", "banana", "cherry", "dragon", "elephant", "forest", "guitar", "horizon",
        "island", "jungle", "kingdom", "lemon", "mountain", "nebula", "ocean", "penguin",
        "quantum", "rainbow", "sunset", "thunder", "umbrella", "volcano", "whisper", "zenith",
        "anchor", "breeze", "crystal", "dolphin", "eclipse", "falcon", "glacier", "harbor",
        "ivory", "jasmine", "kiwi", "lantern", "marble", "nature", "orchid", "phoenix",
        "quartz", "river", "shadow", "tiger", "unity", "velvet", "willow", "xerox",
        "yellow", "zephyr", "amber", "bronze", "cobalt", "dusk", "ember", "frost",
        "golden", "haze", "indigo", "jade", "karma", "lunar", "mist", "noble"
    ]
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        self._setup_ui()
        self._generate_password()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        title = QLabel("🔑 Password Generator")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f9fafb;
            }
        """)
        layout.addWidget(title)
        
        # Tabs for password types
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
        """)
        
        # Random Password Tab
        tabs.addTab(self._create_random_tab(), "🎲 Random")
        
        # Passphrase Tab
        tabs.addTab(self._create_passphrase_tab(), "📝 Passphrase")
        
        # PIN Tab
        tabs.addTab(self._create_pin_tab(), "🔢 PIN")
        
        layout.addWidget(tabs, 1)
        
        # History section
        self.history_frame = QFrame(self)
        self.history_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 8px;
                border: 1px solid #374151;
            }
        """)
        history_layout = QVBoxLayout(self.history_frame)
        history_layout.setContentsMargins(16, 12, 16, 12)
        
        history_header = QHBoxLayout()
        history_label = QLabel("📜 Recent Passwords")
        history_label.setStyleSheet("color: #f9fafb; font-weight: bold;")
        history_header.addWidget(history_label)
        history_header.addStretch()
        
        clear_btn = QPushButton("🗑️ Clear History")
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
        clear_btn.clicked.connect(self._clear_history)
        history_header.addWidget(clear_btn)
        
        history_layout.addLayout(history_header)
        
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(120)
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 4px;
                color: #e5e7eb;
                font-family: 'Consolas', monospace;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #374151;
            }
            QListWidget::item:selected {
                background-color: #374151;
            }
        """)
        self.history_list.itemDoubleClicked.connect(self._copy_history_item)
        history_layout.addWidget(self.history_list)
        
        layout.addWidget(self.history_frame)
        
        # Load history
        self._load_history()
    
    def _create_random_tab(self) -> QWidget:
        """Create random password tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Password display
        self.password_frame = QFrame(self)
        self.password_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border-radius: 12px;
                border: 2px solid #374151;
            }
        """)
        password_layout = QVBoxLayout(self.password_frame)
        password_layout.setContentsMargins(20, 20, 20, 20)
        
        self.password_display = QLineEdit()
        self.password_display.setReadOnly(True)
        self.password_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.password_display.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                color: #10b981;
                font-family: 'Consolas', monospace;
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        password_layout.addWidget(self.password_display)
        
        # Strength bar
        strength_layout = QHBoxLayout()
        self.strength_bar = PasswordStrengthBar()
        strength_layout.addWidget(self.strength_bar)
        
        self.strength_label = QLabel("Strong")
        self.strength_label.setStyleSheet("color: #9ca3af; margin-left: 8px;")
        strength_layout.addWidget(self.strength_label)
        
        self.entropy_label = QLabel("~80 bits")
        self.entropy_label.setStyleSheet("color: #6b7280;")
        strength_layout.addWidget(self.entropy_label)
        
        password_layout.addLayout(strength_layout)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        generate_btn = QPushButton("🔄 Generate")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #818cf8;
            }
        """)
        generate_btn.clicked.connect(self._generate_password)
        btn_layout.addWidget(generate_btn)
        
        copy_btn = QPushButton("📋 Copy")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        copy_btn.clicked.connect(self._copy_password)
        btn_layout.addWidget(copy_btn)
        
        password_layout.addLayout(btn_layout)
        
        layout.addWidget(self.password_frame)
        
        # Options
        self.options_frame = QFrame(self)
        self.options_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border-radius: 8px;
                border: 1px solid #374151;
            }
        """)
        options_layout = QVBoxLayout(self.options_frame)
        options_layout.setContentsMargins(16, 16, 16, 16)
        options_layout.setSpacing(12)
        
        # Length slider
        length_layout = QHBoxLayout()
        length_label = QLabel("Length:")
        length_label.setStyleSheet("color: #9ca3af;")
        length_layout.addWidget(length_label)
        
        self.length_slider = QSlider(Qt.Orientation.Horizontal)
        self.length_slider.setRange(8, 64)
        self.length_slider.setValue(16)
        self.length_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #374151;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #6366f1;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #6366f1;
                border-radius: 4px;
            }
        """)
        self.length_slider.valueChanged.connect(self._on_length_changed)
        length_layout.addWidget(self.length_slider, 1)
        
        self.length_value = QLabel("16")
        self.length_value.setFixedWidth(30)
        self.length_value.setStyleSheet("color: #f9fafb; font-weight: bold;")
        length_layout.addWidget(self.length_value)
        
        options_layout.addLayout(length_layout)
        
        # Character options
        char_layout = QGridLayout()
        char_layout.setSpacing(12)
        
        self.uppercase_check = QCheckBox("ABC Uppercase")
        self.uppercase_check.setChecked(True)
        self.uppercase_check.setStyleSheet("color: #e5e7eb;")
        self.uppercase_check.stateChanged.connect(self._generate_password)
        char_layout.addWidget(self.uppercase_check, 0, 0)
        
        self.lowercase_check = QCheckBox("abc Lowercase")
        self.lowercase_check.setChecked(True)
        self.lowercase_check.setStyleSheet("color: #e5e7eb;")
        self.lowercase_check.stateChanged.connect(self._generate_password)
        char_layout.addWidget(self.lowercase_check, 0, 1)
        
        self.numbers_check = QCheckBox("123 Numbers")
        self.numbers_check.setChecked(True)
        self.numbers_check.setStyleSheet("color: #e5e7eb;")
        self.numbers_check.stateChanged.connect(self._generate_password)
        char_layout.addWidget(self.numbers_check, 1, 0)
        
        self.symbols_check = QCheckBox("!@# Symbols")
        self.symbols_check.setChecked(True)
        self.symbols_check.setStyleSheet("color: #e5e7eb;")
        self.symbols_check.stateChanged.connect(self._generate_password)
        char_layout.addWidget(self.symbols_check, 1, 1)
        
        self.exclude_similar = QCheckBox("Exclude similar (0O, 1lI)")
        self.exclude_similar.setStyleSheet("color: #9ca3af;")
        self.exclude_similar.stateChanged.connect(self._generate_password)
        char_layout.addWidget(self.exclude_similar, 2, 0)
        
        self.exclude_ambiguous = QCheckBox("Exclude ambiguous ({}[])")
        self.exclude_ambiguous.setStyleSheet("color: #9ca3af;")
        self.exclude_ambiguous.stateChanged.connect(self._generate_password)
        char_layout.addWidget(self.exclude_ambiguous, 2, 1)
        
        options_layout.addLayout(char_layout)
        
        layout.addWidget(self.options_frame)
        layout.addStretch()
        
        return widget
    
    def _create_passphrase_tab(self) -> QWidget:
        """Create passphrase tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Passphrase display
        self.passphrase_frame = QFrame(self)
        self.passphrase_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border-radius: 12px;
                border: 2px solid #374151;
            }
        """)
        passphrase_layout = QVBoxLayout(self.passphrase_frame)
        passphrase_layout.setContentsMargins(20, 20, 20, 20)
        
        self.passphrase_display = QLineEdit()
        self.passphrase_display.setReadOnly(True)
        self.passphrase_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.passphrase_display.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                color: #8b5cf6;
                font-family: 'Consolas', monospace;
                font-size: 20px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        passphrase_layout.addWidget(self.passphrase_display)
        
        # Strength bar
        pp_strength_layout = QHBoxLayout()
        self.pp_strength_bar = PasswordStrengthBar()
        pp_strength_layout.addWidget(self.pp_strength_bar)
        
        self.pp_strength_label = QLabel("Strong")
        self.pp_strength_label.setStyleSheet("color: #9ca3af; margin-left: 8px;")
        pp_strength_layout.addWidget(self.pp_strength_label)
        
        passphrase_layout.addLayout(pp_strength_layout)
        
        # Buttons
        pp_btn_layout = QHBoxLayout()
        
        generate_pp_btn = QPushButton("🔄 Generate")
        generate_pp_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #a78bfa;
            }
        """)
        generate_pp_btn.clicked.connect(self._generate_passphrase)
        pp_btn_layout.addWidget(generate_pp_btn)
        
        copy_pp_btn = QPushButton("📋 Copy")
        copy_pp_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        copy_pp_btn.clicked.connect(self._copy_passphrase)
        pp_btn_layout.addWidget(copy_pp_btn)
        
        passphrase_layout.addLayout(pp_btn_layout)
        
        layout.addWidget(self.passphrase_frame)
        
        # Options
        self.pp_options_frame = QFrame(self)
        self.pp_options_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border-radius: 8px;
                border: 1px solid #374151;
            }
        """)
        pp_options_layout = QVBoxLayout(self.pp_options_frame)
        pp_options_layout.setContentsMargins(16, 16, 16, 16)
        
        # Word count
        words_layout = QHBoxLayout()
        words_label = QLabel("Words:")
        words_label.setStyleSheet("color: #9ca3af;")
        words_layout.addWidget(words_label)
        
        self.words_spin = QSpinBox()
        self.words_spin.setRange(3, 10)
        self.words_spin.setValue(4)
        self.words_spin.setStyleSheet("""
            QSpinBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px;
                color: #e5e7eb;
            }
        """)
        self.words_spin.valueChanged.connect(self._generate_passphrase)
        words_layout.addWidget(self.words_spin)
        words_layout.addStretch()
        
        # Separator
        sep_label = QLabel("Separator:")
        sep_label.setStyleSheet("color: #9ca3af;")
        words_layout.addWidget(sep_label)
        
        self.separator_combo = QComboBox()
        self.separator_combo.addItems(["-", "_", ".", " ", ",", "|"])
        self.separator_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px 12px;
                color: #e5e7eb;
            }
        """)
        self.separator_combo.currentTextChanged.connect(self._generate_passphrase)
        words_layout.addWidget(self.separator_combo)
        
        pp_options_layout.addLayout(words_layout)
        
        # Capitalize and numbers
        pp_char_layout = QHBoxLayout()
        
        self.capitalize_check = QCheckBox("Capitalize Words")
        self.capitalize_check.setChecked(True)
        self.capitalize_check.setStyleSheet("color: #e5e7eb;")
        self.capitalize_check.stateChanged.connect(self._generate_passphrase)
        pp_char_layout.addWidget(self.capitalize_check)
        
        self.add_numbers_check = QCheckBox("Add Numbers")
        self.add_numbers_check.setStyleSheet("color: #e5e7eb;")
        self.add_numbers_check.stateChanged.connect(self._generate_passphrase)
        pp_char_layout.addWidget(self.add_numbers_check)
        
        pp_char_layout.addStretch()
        pp_options_layout.addLayout(pp_char_layout)
        
        layout.addWidget(self.pp_options_frame)
        layout.addStretch()
        
        # Generate initial passphrase
        self._generate_passphrase()
        
        return widget
    
    def _create_pin_tab(self) -> QWidget:
        """Create PIN tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # PIN display
        self.pin_frame = QFrame(self)
        self.pin_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border-radius: 12px;
                border: 2px solid #374151;
            }
        """)
        pin_layout = QVBoxLayout(self.pin_frame)
        pin_layout.setContentsMargins(20, 30, 20, 30)
        
        self.pin_display = QLineEdit()
        self.pin_display.setReadOnly(True)
        self.pin_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pin_display.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                color: #f59e0b;
                font-family: 'Consolas', monospace;
                font-size: 48px;
                font-weight: bold;
                letter-spacing: 16px;
            }
        """)
        pin_layout.addWidget(self.pin_display)
        
        # Buttons
        pin_btn_layout = QHBoxLayout()
        
        generate_pin_btn = QPushButton("🔄 Generate")
        generate_pin_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #fbbf24;
            }
        """)
        generate_pin_btn.clicked.connect(self._generate_pin)
        pin_btn_layout.addWidget(generate_pin_btn)
        
        copy_pin_btn = QPushButton("📋 Copy")
        copy_pin_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        copy_pin_btn.clicked.connect(self._copy_pin)
        pin_btn_layout.addWidget(copy_pin_btn)
        
        pin_layout.addLayout(pin_btn_layout)
        
        layout.addWidget(self.pin_frame)
        
        # PIN length
        self.pin_options_frame = QFrame(self)
        self.pin_options_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border-radius: 8px;
                border: 1px solid #374151;
            }
        """)
        pin_options_layout = QVBoxLayout(self.pin_options_frame)
        pin_options_layout.setContentsMargins(16, 16, 16, 16)
        
        pin_length_layout = QHBoxLayout()
        pin_length_label = QLabel("PIN Length:")
        pin_length_label.setStyleSheet("color: #9ca3af;")
        pin_length_layout.addWidget(pin_length_label)
        
        self.pin_length_spin = QSpinBox()
        self.pin_length_spin.setRange(4, 12)
        self.pin_length_spin.setValue(6)
        self.pin_length_spin.setStyleSheet("""
            QSpinBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px;
                color: #e5e7eb;
            }
        """)
        self.pin_length_spin.valueChanged.connect(self._generate_pin)
        pin_length_layout.addWidget(self.pin_length_spin)
        pin_length_layout.addStretch()
        
        pin_options_layout.addLayout(pin_length_layout)
        
        layout.addWidget(self.pin_options_frame)
        layout.addStretch()
        
        # Generate initial PIN
        self._generate_pin()
        
        return widget
    
    def _generate_password(self):
        """Generate random password"""
        length = self.length_slider.value()
        
        # Build character set
        charset = ""
        if self.uppercase_check.isChecked():
            charset += string.ascii_uppercase
        if self.lowercase_check.isChecked():
            charset += string.ascii_lowercase
        if self.numbers_check.isChecked():
            charset += string.digits
        if self.symbols_check.isChecked():
            charset += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        if not charset:
            charset = string.ascii_letters
        
        # Exclusions
        if self.exclude_similar.isChecked():
            charset = charset.translate(str.maketrans('', '', '0O1lI'))
        if self.exclude_ambiguous.isChecked():
            charset = charset.translate(str.maketrans('', '', '{}[]()'))
        
        # Generate
        password = ''.join(secrets.choice(charset) for _ in range(length))
        self.password_display.setText(password)
        
        # Calculate strength
        entropy = len(password) * math.log2(len(charset))
        strength = min(100, int(entropy / 128 * 100))
        
        self.strength_bar.setValue(strength)
        self.entropy_label.setText(f"~{int(entropy)} bits")
        
        if strength < 20:
            self.strength_label.setText("Very Weak")
        elif strength < 40:
            self.strength_label.setText("Weak")
        elif strength < 60:
            self.strength_label.setText("Fair")
        elif strength < 80:
            self.strength_label.setText("Strong")
        else:
            self.strength_label.setText("Very Strong")
        
        # Save to history
        self._save_to_history(password, "password")
    
    def _generate_passphrase(self):
        """Generate passphrase"""
        word_count = self.words_spin.value()
        separator = self.separator_combo.currentText()
        capitalize = self.capitalize_check.isChecked()
        add_numbers = self.add_numbers_check.isChecked()
        
        words = [secrets.choice(self.WORD_LIST) for _ in range(word_count)]
        
        if capitalize:
            words = [w.capitalize() for w in words]
        
        if add_numbers:
            words.append(str(secrets.randbelow(100)))
        
        passphrase = separator.join(words)
        self.passphrase_display.setText(passphrase)
        
        # Calculate strength (assuming ~64 words in list)
        entropy = word_count * math.log2(len(self.WORD_LIST))
        if add_numbers:
            entropy += math.log2(100)
        
        strength = min(100, int(entropy / 128 * 100))
        self.pp_strength_bar.setValue(strength)
        
        if strength < 40:
            self.pp_strength_label.setText("Fair")
        elif strength < 60:
            self.pp_strength_label.setText("Good")
        else:
            self.pp_strength_label.setText("Strong")
        
        # Save to history
        self._save_to_history(passphrase, "passphrase")
    
    def _generate_pin(self):
        """Generate PIN"""
        length = self.pin_length_spin.value()
        pin = ''.join(str(secrets.randbelow(10)) for _ in range(length))
        self.pin_display.setText(pin)
        
        # Save to history
        self._save_to_history(pin, "pin")
    
    def _on_length_changed(self, value: int):
        """Handle length slider change"""
        self.length_value.setText(str(value))
        self._generate_password()
    
    def _copy_password(self):
        """Copy password to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.password_display.text())
    
    def _copy_passphrase(self):
        """Copy passphrase to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.passphrase_display.text())
    
    def _copy_pin(self):
        """Copy PIN to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.pin_display.text())
    
    def _save_to_history(self, password: str, password_type: str):
        """Save password to database history"""
        from core.database import get_session, PasswordHistory
        
        # Hash the password for storage
        pw_hash = hashlib.sha256(password.encode()).hexdigest()[:16]
        
        with get_session() as session:
            history = PasswordHistory(
                password_hash=pw_hash,
                password_type=password_type,
                length=len(password),
                display_preview=password[:4] + "****" + password[-4:] if len(password) > 8 else "****"
            )
            session.add(history)
            session.commit()
        
        self._load_history()
    
    def _load_history(self):
        """Load password history"""
        self.history_list.clear()
        
        from core.database import get_session, PasswordHistory
        
        with get_session() as session:
            history = session.query(PasswordHistory).order_by(
                PasswordHistory.created_at.desc()
            ).limit(10).all()
            
            for h in history:
                item = QListWidgetItem(f"{h.password_type.upper()} | {h.display_preview} | {h.length} chars")
                self.history_list.addItem(item)
    
    def _copy_history_item(self, item: QListWidgetItem):
        """Copy history item preview"""
        # Note: We only store hashes, so we can only copy the preview
        text = item.text().split(" | ")[1]
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
    
    def _clear_history(self):
        """Clear password history"""
        from core.database import get_session, PasswordHistory
        
        with get_session() as session:
            session.query(PasswordHistory).delete()
            session.commit()
        
        self.history_list.clear()

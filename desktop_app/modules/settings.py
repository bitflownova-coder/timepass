"""
Settings Dialog - Application configuration
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QSpinBox, QCheckBox,
    QComboBox, QPushButton, QFormLayout, QGroupBox,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    """Application settings dialog"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #1f2937;
            }
            QLabel {
                color: #e5e7eb;
            }
            QGroupBox {
                color: #e5e7eb;
                border: 1px solid #374151;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
            QLineEdit, QSpinBox, QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px;
                color: #e5e7eb;
            }
            QCheckBox {
                color: #e5e7eb;
            }
            QPushButton {
                background-color: #6366f1;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #818cf8;
            }
            QPushButton#cancelBtn {
                background-color: #374151;
            }
            QPushButton#cancelBtn:hover {
                background-color: #4b5563;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("⚙️ Settings")
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
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
                padding: 8px 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #1f2937;
                color: #e5e7eb;
            }
        """)
        
        # General tab
        general_tab = self._create_general_tab()
        tabs.addTab(general_tab, "General")
        
        # Time Tracker tab
        time_tab = self._create_time_tracker_tab()
        tabs.addTab(time_tab, "Time Tracker")
        
        # Finance tab
        finance_tab = self._create_finance_tab()
        tabs.addTab(finance_tab, "Finance")
        
        # Crawler tab
        crawler_tab = self._create_crawler_tab()
        tabs.addTab(crawler_tab, "Crawler")
        
        layout.addWidget(tabs, 1)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Appearance
        appearance = QGroupBox("Appearance")
        form = QFormLayout(appearance)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "dark_teal.xml",
            "dark_blue.xml", 
            "dark_purple.xml",
            "light_teal.xml",
            "light_blue.xml"
        ])
        form.addRow("Theme:", self.theme_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        form.addRow("Font Size:", self.font_size_spin)
        
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            "Consolas",
            "Fira Code",
            "JetBrains Mono",
            "Source Code Pro",
            "Cascadia Code"
        ])
        form.addRow("Code Font:", self.font_family_combo)
        
        layout.addWidget(appearance)
        
        # Behavior
        behavior = QGroupBox("Behavior")
        form2 = QFormLayout(behavior)
        
        self.auto_save_check = QCheckBox("Enable auto-save")
        form2.addRow(self.auto_save_check)
        
        self.recent_files_spin = QSpinBox()
        self.recent_files_spin.setRange(5, 50)
        form2.addRow("Max Recent Files:", self.recent_files_spin)
        
        layout.addWidget(behavior)
        layout.addStretch()
        
        return widget
    
    def _create_time_tracker_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        group = QGroupBox("Time Tracking Settings")
        form = QFormLayout(group)
        
        self.hourly_rate_spin = QSpinBox()
        self.hourly_rate_spin.setRange(0, 10000)
        self.hourly_rate_spin.setPrefix("₹ ")
        form.addRow("Default Hourly Rate:", self.hourly_rate_spin)
        
        self.auto_pause_spin = QSpinBox()
        self.auto_pause_spin.setRange(0, 60)
        self.auto_pause_spin.setSuffix(" min")
        self.auto_pause_spin.setSpecialValueText("Disabled")
        form.addRow("Auto-pause after idle:", self.auto_pause_spin)
        
        self.reminder_spin = QSpinBox()
        self.reminder_spin.setRange(0, 120)
        self.reminder_spin.setSuffix(" min")
        self.reminder_spin.setSpecialValueText("Disabled")
        form.addRow("Timer reminder interval:", self.reminder_spin)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _create_finance_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        group = QGroupBox("Finance Settings")
        form = QFormLayout(group)
        
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["INR", "USD", "EUR", "GBP", "AUD"])
        form.addRow("Currency:", self.currency_combo)
        
        self.currency_symbol_edit = QLineEdit()
        form.addRow("Currency Symbol:", self.currency_symbol_edit)
        
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems([
            "dd/MM/yyyy",
            "MM/dd/yyyy",
            "yyyy-MM-dd"
        ])
        form.addRow("Date Format:", self.date_format_combo)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _create_crawler_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        group = QGroupBox("Crawler Settings")
        form = QFormLayout(group)
        
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 10)
        form.addRow("Default Depth:", self.depth_spin)
        
        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setRange(1, 10)
        form.addRow("Concurrency:", self.concurrency_spin)
        
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 10)
        self.delay_spin.setSuffix(" sec")
        form.addRow("Delay Between Requests:", self.delay_spin)
        
        self.download_images_check = QCheckBox("Download images")
        form.addRow(self.download_images_check)
        
        self.download_docs_check = QCheckBox("Download documents (PDF, DOC)")
        form.addRow(self.download_docs_check)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _load_settings(self):
        """Load current settings"""
        # General
        self.theme_combo.setCurrentText(self.config.get("theme", "dark_teal.xml"))
        self.font_size_spin.setValue(self.config.get("font_size", 10))
        self.font_family_combo.setCurrentText(self.config.get("font_family", "Consolas"))
        self.auto_save_check.setChecked(self.config.get("quick_notes.auto_save", True))
        self.recent_files_spin.setValue(self.config.get("max_recent_files", 10))
        
        # Time Tracker
        self.hourly_rate_spin.setValue(int(self.config.get("time_tracker.default_hourly_rate", 0)))
        self.auto_pause_spin.setValue(self.config.get("time_tracker.auto_pause_after_mins", 0))
        self.reminder_spin.setValue(self.config.get("time_tracker.reminder_interval_mins", 30))
        
        # Finance
        self.currency_combo.setCurrentText(self.config.get("finance.currency", "INR"))
        self.currency_symbol_edit.setText(self.config.get("finance.currency_symbol", "₹"))
        self.date_format_combo.setCurrentText(self.config.get("finance.date_format", "dd/MM/yyyy"))
        
        # Crawler
        self.depth_spin.setValue(self.config.get("crawler.default_depth", 2))
        self.concurrency_spin.setValue(self.config.get("crawler.default_concurrency", 3))
        self.delay_spin.setValue(self.config.get("crawler.default_delay", 1))
        self.download_images_check.setChecked(self.config.get("crawler.download_images", True))
        self.download_docs_check.setChecked(self.config.get("crawler.download_documents", True))
    
    def _save_settings(self):
        """Save settings"""
        # General
        self.config.set("theme", self.theme_combo.currentText(), save=False)
        self.config.set("font_size", self.font_size_spin.value(), save=False)
        self.config.set("font_family", self.font_family_combo.currentText(), save=False)
        self.config.set("quick_notes.auto_save", self.auto_save_check.isChecked(), save=False)
        self.config.set("max_recent_files", self.recent_files_spin.value(), save=False)
        
        # Time Tracker
        self.config.set("time_tracker.default_hourly_rate", float(self.hourly_rate_spin.value()), save=False)
        self.config.set("time_tracker.auto_pause_after_mins", self.auto_pause_spin.value(), save=False)
        self.config.set("time_tracker.reminder_interval_mins", self.reminder_spin.value(), save=False)
        
        # Finance
        self.config.set("finance.currency", self.currency_combo.currentText(), save=False)
        self.config.set("finance.currency_symbol", self.currency_symbol_edit.text(), save=False)
        self.config.set("finance.date_format", self.date_format_combo.currentText(), save=False)
        
        # Crawler
        self.config.set("crawler.default_depth", self.depth_spin.value(), save=False)
        self.config.set("crawler.default_concurrency", self.concurrency_spin.value(), save=False)
        self.config.set("crawler.default_delay", self.delay_spin.value(), save=False)
        self.config.set("crawler.download_images", self.download_images_check.isChecked(), save=False)
        self.config.set("crawler.download_documents", self.download_docs_check.isChecked(), save=True)
        
        QMessageBox.information(self, "Settings", "Settings saved successfully!")
        self.accept()

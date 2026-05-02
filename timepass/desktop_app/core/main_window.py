"""
Main Application Window with Sidebar Navigation
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QPushButton, QLabel, QFrame,
    QScrollArea, QSizePolicy, QSpacerItem, QToolTip
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette
from typing import Dict, List, Callable
import importlib

from .config import Config
from .database import Database


class SidebarButton(QPushButton):
    """Custom sidebar navigation button"""
    
    def __init__(self, text: str, icon_name: str, module_id: str, parent=None):
        super().__init__(parent)
        self.module_id = module_id
        self._text = text
        self._icon_name = icon_name
        self._is_selected = False
        self._is_collapsed = False
        
        self.setCheckable(True)
        self.setMinimumHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_appearance()
    
    def _update_appearance(self):
        """Update button appearance based on state"""
        if self._is_collapsed:
            self.setText("")
            self.setToolTip(self._text)
            self.setFixedWidth(50)
        else:
            self.setText(f"  {self._text}")
            self.setToolTip("")
            self.setMinimumWidth(200)
            self.setMaximumWidth(250)
        
        # Icon setup would go here (using icon fonts or SVG)
        base_style = """
            QPushButton {
                text-align: left;
                padding: 10px 15px;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }
        """
        
        if self._is_selected:
            self.setStyleSheet(base_style + """
                QPushButton {
                    background-color: rgba(99, 102, 241, 0.2);
                    color: #818cf8;
                }
            """)
        else:
            self.setStyleSheet(base_style + """
                QPushButton {
                    background-color: transparent;
                    color: #9ca3af;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.05);
                    color: #e5e7eb;
                }
            """)
    
    def set_selected(self, selected: bool):
        """Set the selected state"""
        self._is_selected = selected
        self._update_appearance()
    
    def set_collapsed(self, collapsed: bool):
        """Set collapsed mode"""
        self._is_collapsed = collapsed
        self._update_appearance()


class Sidebar(QFrame):
    """Collapsible sidebar navigation"""
    
    module_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_collapsed = False
        self._buttons: Dict[str, SidebarButton] = {}
        self._current_module = None
        
        self.setObjectName("sidebar")
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup sidebar UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(4)
        
        # Logo/Brand section
        brand_layout = QHBoxLayout()
        self.brand_label = QLabel("🚀 Bitflow")
        self.brand_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #818cf8;
                padding: 10px 8px;
            }
        """)
        brand_layout.addWidget(self.brand_label)
        brand_layout.addStretch()
        
        # Collapse button
        self.collapse_btn = QPushButton("◀")
        self.collapse_btn.setFixedSize(28, 28)
        self.collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.collapse_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                color: #6b7280;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.collapse_btn.clicked.connect(self._toggle_collapse)
        brand_layout.addWidget(self.collapse_btn)
        
        layout.addLayout(brand_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #374151;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        layout.addSpacing(8)
        
        # Navigation buttons scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                width: 6px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #4b5563;
                border-radius: 3px;
            }
        """)
        
        self.nav_widget = QWidget()
        self.nav_layout = QVBoxLayout(self.nav_widget)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(2)
        scroll.setWidget(self.nav_widget)
        
        layout.addWidget(scroll, 1)
        
        # Bottom section
        layout.addSpacing(8)
        settings_btn = SidebarButton("Settings", "settings", "settings")
        settings_btn.clicked.connect(lambda: self._on_button_clicked("settings"))
        self._buttons["settings"] = settings_btn
        layout.addWidget(settings_btn)
        
        self.setStyleSheet("""
            #sidebar {
                background-color: #111827;
                border-right: 1px solid #1f2937;
            }
        """)
        self.setMinimumWidth(220)
        self.setMaximumWidth(260)
    
    def add_section(self, title: str):
        """Add a section header to navigation"""
        if not self._is_collapsed:
            label = QLabel(title.upper())
            label.setStyleSheet("""
                QLabel {
                    color: #6b7280;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 12px 15px 6px 15px;
                    letter-spacing: 1px;
                }
            """)
            self.nav_layout.addWidget(label)
    
    def add_module(self, module_id: str, title: str, icon: str):
        """Add a module button to navigation"""
        btn = SidebarButton(title, icon, module_id)
        btn.clicked.connect(lambda: self._on_button_clicked(module_id))
        self._buttons[module_id] = btn
        self.nav_layout.addWidget(btn)
    
    def add_spacer(self):
        """Add spacing between sections"""
        self.nav_layout.addSpacing(8)
    
    def _on_button_clicked(self, module_id: str):
        """Handle button click"""
        if self._current_module:
            self._buttons[self._current_module].set_selected(False)
        
        self._buttons[module_id].set_selected(True)
        self._current_module = module_id
        self.module_selected.emit(module_id)
    
    def select_module(self, module_id: str):
        """Programmatically select a module"""
        if module_id in self._buttons:
            self._on_button_clicked(module_id)
    
    def _toggle_collapse(self):
        """Toggle sidebar collapse state"""
        self._is_collapsed = not self._is_collapsed
        
        if self._is_collapsed:
            self.brand_label.setText("🚀")
            self.collapse_btn.setText("▶")
            self.setFixedWidth(66)
        else:
            self.brand_label.setText("🚀 Bitflow")
            self.collapse_btn.setText("◀")
            self.setMinimumWidth(220)
            self.setMaximumWidth(260)
        
        # Update all buttons
        for btn in self._buttons.values():
            btn.set_collapsed(self._is_collapsed)
        
        # Hide section labels when collapsed
        for i in range(self.nav_layout.count()):
            item = self.nav_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QLabel):
                    widget.setVisible(not self._is_collapsed)


class MainWindow(QMainWindow):
    """Main Application Window"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.db = Database()
        self._modules: Dict[str, QWidget] = {}
        
        self._setup_window()
        self._setup_ui()
        self._setup_modules()
        self._load_state()
    
    def _setup_window(self):
        """Configure main window"""
        self.setWindowTitle("Bitflow Developer Toolkit")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 850)
        
        # Center on screen
        screen = self.screen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def _setup_ui(self):
        """Setup main UI layout"""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.module_selected.connect(self._on_module_selected)
        layout.addWidget(self.sidebar)
        
        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
            }
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        
        layout.addWidget(content_frame, 1)
    
    def _setup_modules(self):
        """Setup all application modules"""
        # Dashboard
        self.sidebar.add_section("Overview")
        self._register_module("dashboard", "Dashboard", "home", "modules.dashboard", "DashboardModule")
        
        self.sidebar.add_spacer()
        
        # Developer Tools
        self.sidebar.add_section("Dev Tools")
        self._register_module("time_tracker", "Time Tracker", "clock", "modules.time_tracker", "TimeTrackerModule")
        self._register_module("quick_notes", "Quick Notes", "note", "modules.quick_notes", "QuickNotesModule")
        self._register_module("snippets", "Snippets", "code", "modules.snippet_manager", "SnippetManagerModule")
        self._register_module("api_tester", "API Tester", "api", "modules.api_tester", "ApiTesterModule")
        
        self.sidebar.add_spacer()
        
        # Formatters & Converters
        self.sidebar.add_section("Tools")
        self._register_module("json_formatter", "JSON/XML", "json", "modules.json_formatter", "JsonFormatterModule")
        self._register_module("regex_tester", "Regex Tester", "regex", "modules.regex_tester", "RegexTesterModule")
        self._register_module("encoder", "Encoder/Decoder", "lock", "modules.encoder_decoder", "EncoderDecoderModule")
        self._register_module("color_converter", "Colors", "palette", "modules.color_converter", "ColorConverterModule")
        
        self.sidebar.add_spacer()
        
        # Generators
        self.sidebar.add_section("Generators")
        self._register_module("password_gen", "Password Gen", "key", "modules.password_generator", "PasswordGeneratorModule")
        self._register_module("qr_gen", "QR Code Gen", "qr", "modules.qr_generator", "QRCodeGeneratorModule")
        self._register_module("lorem_gen", "Lorem Gen", "text", "modules.lorem_generator", "LoremGeneratorModule")
        self._register_module("markdown", "Markdown", "markdown", "modules.markdown_previewer", "MarkdownPreviewerModule")
        
        self.sidebar.add_spacer()
        
        # System Tools
        self.sidebar.add_section("System")
        self._register_module("port_scanner", "Port Scanner", "network", "modules.port_scanner", "PortScannerModule")
        self._register_module("log_viewer", "Log Viewer", "log", "modules.log_viewer", "LogViewerModule")
        self._register_module("env_manager", "Environment", "env", "modules.env_manager", "EnvManagerModule")
        
        self.sidebar.add_spacer()
        
        # Business Tools
        self.sidebar.add_section("Business")
        self._register_module("crawler", "Web Crawler", "spider", "modules.web_crawler", "WebCrawlerModule")
        self._register_module("finance", "Finance", "money", "modules.finance", "FinanceModule")
        
        # Select dashboard by default
        self.sidebar.select_module("dashboard")
    
    def _register_module(self, module_id: str, title: str, icon: str, 
                         module_path: str, class_name: str):
        """Register a module for lazy loading"""
        self.sidebar.add_module(module_id, title, icon)
        # Store module info for lazy loading
        self._modules[module_id] = {
            "path": module_path,
            "class": class_name,
            "widget": None
        }
    
    def _on_module_selected(self, module_id: str):
        """Handle module selection"""
        if module_id not in self._modules:
            if module_id == "settings":
                self._show_settings()
            return
        
        module_info = self._modules[module_id]
        
        # Lazy load module if not loaded
        if module_info["widget"] is None:
            try:
                module = importlib.import_module(module_info["path"])
                module_class = getattr(module, module_info["class"])
                widget = module_class(self.db, self.config)
                module_info["widget"] = widget
                self.stack.addWidget(widget)
            except Exception as e:
                # Show error placeholder
                error_widget = self._create_placeholder(module_id, str(e))
                module_info["widget"] = error_widget
                self.stack.addWidget(error_widget)
        
        self.stack.setCurrentWidget(module_info["widget"])
    
    def _create_placeholder(self, module_id: str, error: str = None) -> QWidget:
        """Create a placeholder widget for unloaded modules"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if error:
            label = QLabel(f"⚠️ Failed to load {module_id}\n\n{error}")
        else:
            label = QLabel(f"🔨 {module_id.replace('_', ' ').title()}\n\nModule loading...")
        
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: #9ca3af;
                font-size: 16px;
                padding: 20px;
            }
        """)
        layout.addWidget(label)
        return widget
    
    def _show_settings(self):
        """Show settings dialog"""
        from modules.settings import SettingsDialog
        dialog = SettingsDialog(self.config, self)
        dialog.exec()
    
    def _load_state(self):
        """Load saved window state"""
        state = self.config.get("window_state", {})
        if state.get("geometry"):
            try:
                from PyQt6.QtCore import QByteArray
                self.restoreGeometry(QByteArray.fromBase64(state["geometry"].encode()))
            except:
                pass
    
    def _save_state(self):
        """Save window state"""
        self.config.set("window_state", {
            "geometry": bytes(self.saveGeometry().toBase64()).decode()
        })
    
    def closeEvent(self, event):
        """Handle window close"""
        self._save_state()
        self.db.close()
        super().closeEvent(event)

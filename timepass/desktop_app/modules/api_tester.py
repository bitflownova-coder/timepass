"""
API Tester Module - Send HTTP requests and inspect responses
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QLineEdit, QTextEdit,
    QComboBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QPlainTextEdit, QSpinBox,
    QCheckBox, QDialog, QFormLayout, QMessageBox,
    QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
from typing import Optional, Dict, List, Any
import json
import time

from core.database import ApiRequest, ApiCollection, ApiHistory, get_session


class RequestThread(QThread):
    """Thread for making HTTP requests"""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, method: str, url: str, headers: Dict, body: str = None, 
                 body_type: str = None, timeout: int = 30):
        super().__init__()
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body
        self.body_type = body_type
        self.timeout = timeout
    
    def run(self):
        try:
            import httpx
            
            start_time = time.time()
            
            # Prepare request kwargs
            kwargs = {
                "timeout": self.timeout,
                "headers": self.headers,
                "follow_redirects": True
            }
            
            # Add body if present
            if self.body and self.method in ["POST", "PUT", "PATCH"]:
                if self.body_type == "json":
                    try:
                        kwargs["json"] = json.loads(self.body)
                    except json.JSONDecodeError:
                        kwargs["content"] = self.body
                elif self.body_type == "form":
                    # Parse form data
                    form_data = {}
                    for line in self.body.split("\n"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            form_data[key.strip()] = value.strip()
                    kwargs["data"] = form_data
                else:
                    kwargs["content"] = self.body
            
            # Make request
            with httpx.Client() as client:
                response = getattr(client, self.method.lower())(self.url, **kwargs)
            
            elapsed = time.time() - start_time
            
            # Parse response
            try:
                response_body = response.text
            except:
                response_body = str(response.content)
            
            result = {
                "status_code": response.status_code,
                "status_text": response.reason_phrase,
                "headers": dict(response.headers),
                "body": response_body,
                "elapsed_ms": int(elapsed * 1000),
                "size_bytes": len(response.content)
            }
            
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))


class HeadersEditor(QTableWidget):
    """Table editor for HTTP headers"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["", "Key", "Value"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.setColumnWidth(0, 30)
        self.verticalHeader().setVisible(False)
        
        self.setStyleSheet("""
            QTableWidget {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 6px;
                gridline-color: #374151;
            }
            QTableWidget::item {
                color: #e5e7eb;
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #374151;
                color: #9ca3af;
                border: none;
                padding: 8px;
            }
        """)
        
        self._add_row()
    
    def _add_row(self):
        """Add a new row"""
        row = self.rowCount()
        self.insertRow(row)
        
        # Enabled checkbox
        check = QCheckBox()
        check.setChecked(True)
        self.setCellWidget(row, 0, check)
        
        # Key and value editors
        self.setItem(row, 1, QTableWidgetItem(""))
        self.setItem(row, 2, QTableWidgetItem(""))
        
        # Auto-add new row when editing last row
        self.cellChanged.connect(self._on_cell_changed)
    
    def _on_cell_changed(self, row: int, col: int):
        """Add new row if needed"""
        if row == self.rowCount() - 1:
            key_item = self.item(row, 1)
            value_item = self.item(row, 2)
            if (key_item and key_item.text()) or (value_item and value_item.text()):
                self.cellChanged.disconnect(self._on_cell_changed)
                self._add_row()
                self.cellChanged.connect(self._on_cell_changed)
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers as dictionary"""
        headers = {}
        for row in range(self.rowCount()):
            check = self.cellWidget(row, 0)
            if check and check.isChecked():
                key_item = self.item(row, 1)
                value_item = self.item(row, 2)
                if key_item and value_item and key_item.text():
                    headers[key_item.text()] = value_item.text()
        return headers
    
    def set_headers(self, headers: Dict[str, str]):
        """Set headers from dictionary"""
        self.setRowCount(0)
        for key, value in headers.items():
            row = self.rowCount()
            self.insertRow(row)
            
            check = QCheckBox()
            check.setChecked(True)
            self.setCellWidget(row, 0, check)
            
            self.setItem(row, 1, QTableWidgetItem(key))
            self.setItem(row, 2, QTableWidgetItem(value))
        
        self._add_row()


class JsonTreeWidget(QTreeWidget):
    """Tree widget for displaying JSON"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Key", "Value", "Type"])
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 6px;
                color: #e5e7eb;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: rgba(99, 102, 241, 0.3);
            }
            QHeaderView::section {
                background-color: #374151;
                color: #9ca3af;
                border: none;
                padding: 6px;
            }
        """)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
    
    def load_json(self, data: Any, parent=None):
        """Load JSON data into tree"""
        self.clear()
        self._add_item(data, self.invisibleRootItem())
        self.expandAll()
    
    def _add_item(self, data: Any, parent: QTreeWidgetItem, key: str = ""):
        """Add item to tree recursively"""
        if isinstance(data, dict):
            for k, v in data.items():
                item = QTreeWidgetItem(parent)
                item.setText(0, str(k))
                self._add_item(v, item, k)
        elif isinstance(data, list):
            for i, v in enumerate(data):
                item = QTreeWidgetItem(parent)
                item.setText(0, f"[{i}]")
                self._add_item(v, item, f"[{i}]")
        else:
            parent.setText(1, str(data))
            type_name = type(data).__name__
            parent.setText(2, type_name)
            
            # Color code by type
            color = "#9ca3af"
            if isinstance(data, str):
                color = "#c3e88d"
            elif isinstance(data, (int, float)):
                color = "#f78c6c"
            elif isinstance(data, bool):
                color = "#c792ea"
            elif data is None:
                color = "#82aaff"
            
            parent.setForeground(1, QColor(color))


class ApiTesterModule(QWidget):
    """API Tester Module"""
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        self._request_thread: Optional[RequestThread] = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🔌 API Tester")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f9fafb;
            }
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Request bar
        self.request_frame = QFrame(self)
        self.request_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 8px;
                border: 1px solid #374151;
            }
        """)
        request_layout = QHBoxLayout(self.request_frame)
        request_layout.setContentsMargins(12, 12, 12, 12)
        
        # Method selector
        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
        self.method_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 10px 16px;
                color: #10b981;
                font-weight: bold;
                min-width: 100px;
            }
        """)
        self.method_combo.currentTextChanged.connect(self._on_method_changed)
        request_layout.addWidget(self.method_combo)
        
        # URL input
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Enter request URL...")
        self.url_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 10px;
                color: #e5e7eb;
                font-size: 14px;
            }
        """)
        request_layout.addWidget(self.url_edit, 1)
        
        # Send button
        self.send_btn = QPushButton("Send ▶")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #818cf8;
            }
            QPushButton:disabled {
                background-color: #4b5563;
            }
        """)
        self.send_btn.clicked.connect(self._send_request)
        request_layout.addWidget(self.send_btn)
        
        layout.addWidget(self.request_frame)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Request panel
        self.request_panel = QFrame(self)
        self.request_panel.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        request_panel_layout = QVBoxLayout(self.request_panel)
        request_panel_layout.setContentsMargins(12, 12, 12, 12)
        
        # Request tabs
        self.request_tabs = QTabWidget()
        self.request_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                background-color: transparent;
                color: #9ca3af;
                padding: 8px 16px;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected {
                color: #6366f1;
                border-bottom: 2px solid #6366f1;
            }
        """)
        
        # Headers tab
        self.headers_editor = HeadersEditor()
        self.request_tabs.addTab(self.headers_editor, "Headers")
        
        # Body tab
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 8, 0, 0)
        
        # Body type selector
        body_type_layout = QHBoxLayout()
        self.body_type_combo = QComboBox()
        self.body_type_combo.addItems(["None", "JSON", "Form Data", "Raw"])
        self.body_type_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px 12px;
                color: #e5e7eb;
            }
        """)
        body_type_layout.addWidget(QLabel("Body Type:"))
        body_type_layout.addWidget(self.body_type_combo)
        body_type_layout.addStretch()
        body_layout.addLayout(body_type_layout)
        
        self.body_edit = QPlainTextEdit()
        self.body_edit.setPlaceholderText("Request body...")
        self.body_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 8px;
                color: #e5e7eb;
                font-family: 'Consolas', monospace;
            }
        """)
        body_layout.addWidget(self.body_edit)
        
        self.request_tabs.addTab(body_widget, "Body")
        
        # Auth tab
        auth_widget = QWidget()
        auth_layout = QFormLayout(auth_widget)
        auth_layout.setContentsMargins(0, 16, 0, 0)
        
        self.auth_type_combo = QComboBox()
        self.auth_type_combo.addItems(["None", "Bearer Token", "Basic Auth", "API Key"])
        self.auth_type_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px 12px;
                color: #e5e7eb;
            }
        """)
        auth_layout.addRow("Auth Type:", self.auth_type_combo)
        
        self.auth_token_edit = QLineEdit()
        self.auth_token_edit.setPlaceholderText("Token / Username")
        self.auth_token_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
            }
        """)
        auth_layout.addRow("Token:", self.auth_token_edit)
        
        self.auth_secret_edit = QLineEdit()
        self.auth_secret_edit.setPlaceholderText("Password / Secret")
        self.auth_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.auth_secret_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
            }
        """)
        auth_layout.addRow("Secret:", self.auth_secret_edit)
        
        self.request_tabs.addTab(auth_widget, "Auth")
        
        request_panel_layout.addWidget(self.request_tabs)
        splitter.addWidget(self.request_panel)
        
        # Response panel
        self.response_panel = QFrame(self)
        self.response_panel.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        response_layout = QVBoxLayout(self.response_panel)
        response_layout.setContentsMargins(12, 12, 12, 12)
        
        # Response header
        response_header = QHBoxLayout()
        
        response_label = QLabel("Response")
        response_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #e5e7eb;
            }
        """)
        response_header.addWidget(response_label)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        response_header.addWidget(self.status_label)
        
        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: #9ca3af;")
        response_header.addWidget(self.time_label)
        
        self.size_label = QLabel()
        self.size_label.setStyleSheet("color: #9ca3af;")
        response_header.addWidget(self.size_label)
        
        response_header.addStretch()
        response_layout.addLayout(response_header)
        
        # Response tabs
        self.response_tabs = QTabWidget()
        self.response_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                background-color: transparent;
                color: #9ca3af;
                padding: 8px 16px;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected {
                color: #10b981;
                border-bottom: 2px solid #10b981;
            }
        """)
        
        # Body tab
        self.response_body = QPlainTextEdit()
        self.response_body.setReadOnly(True)
        self.response_body.setStyleSheet("""
            QPlainTextEdit {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 8px;
                color: #e5e7eb;
                font-family: 'Consolas', monospace;
            }
        """)
        self.response_tabs.addTab(self.response_body, "Body")
        
        # Pretty tab (JSON tree)
        self.json_tree = JsonTreeWidget()
        self.response_tabs.addTab(self.json_tree, "Pretty")
        
        # Headers tab
        self.response_headers = QPlainTextEdit()
        self.response_headers.setReadOnly(True)
        self.response_headers.setStyleSheet("""
            QPlainTextEdit {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 8px;
                color: #e5e7eb;
                font-family: 'Consolas', monospace;
            }
        """)
        self.response_tabs.addTab(self.response_headers, "Headers")
        
        response_layout.addWidget(self.response_tabs)
        splitter.addWidget(self.response_panel)
        
        splitter.setSizes([250, 350])
        layout.addWidget(splitter, 1)
    
    def _on_method_changed(self, method: str):
        """Handle method change"""
        # Show/hide body tab based on method
        has_body = method in ["POST", "PUT", "PATCH"]
        # Could disable body input here if needed
    
    def _send_request(self):
        """Send the HTTP request"""
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Validation", "Please enter a URL.")
            return
        
        # Add protocol if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        method = self.method_combo.currentText()
        headers = self.headers_editor.get_headers()
        
        # Add auth headers
        auth_type = self.auth_type_combo.currentText()
        if auth_type == "Bearer Token" and self.auth_token_edit.text():
            headers["Authorization"] = f"Bearer {self.auth_token_edit.text()}"
        elif auth_type == "Basic Auth":
            import base64
            credentials = f"{self.auth_token_edit.text()}:{self.auth_secret_edit.text()}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        elif auth_type == "API Key" and self.auth_token_edit.text():
            headers["X-API-Key"] = self.auth_token_edit.text()
        
        # Body
        body = None
        body_type = None
        if self.body_type_combo.currentText() != "None":
            body = self.body_edit.toPlainText()
            body_type = self.body_type_combo.currentText().lower().replace(" ", "_")
            if body_type == "json" and "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"
        
        # Disable send button
        self.send_btn.setEnabled(False)
        self.send_btn.setText("Sending...")
        
        # Clear previous response
        self.response_body.clear()
        self.response_headers.clear()
        self.json_tree.clear()
        self.status_label.clear()
        self.time_label.clear()
        self.size_label.clear()
        
        # Start request thread
        self._request_thread = RequestThread(method, url, headers, body, body_type)
        self._request_thread.finished.connect(self._on_request_finished)
        self._request_thread.error.connect(self._on_request_error)
        self._request_thread.start()
    
    def _on_request_finished(self, result: Dict):
        """Handle successful response"""
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send ▶")
        
        # Status
        status_code = result["status_code"]
        status_text = result.get("status_text", "")
        
        if 200 <= status_code < 300:
            color = "#10b981"
            bg = "rgba(16, 185, 129, 0.2)"
        elif 300 <= status_code < 400:
            color = "#f59e0b"
            bg = "rgba(245, 158, 11, 0.2)"
        else:
            color = "#ef4444"
            bg = "rgba(239, 68, 68, 0.2)"
        
        self.status_label.setText(f"{status_code} {status_text}")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {color};
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: bold;
            }}
        """)
        
        # Time and size
        self.time_label.setText(f"⏱️ {result['elapsed_ms']}ms")
        size_kb = result['size_bytes'] / 1024
        self.size_label.setText(f"📦 {size_kb:.1f}KB")
        
        # Body
        body = result["body"]
        self.response_body.setPlainText(body)
        
        # Try to parse as JSON for pretty view
        try:
            json_data = json.loads(body)
            self.json_tree.load_json(json_data)
            # Pretty print in body too
            self.response_body.setPlainText(json.dumps(json_data, indent=2))
        except json.JSONDecodeError:
            pass
        
        # Headers
        headers_text = "\n".join(f"{k}: {v}" for k, v in result["headers"].items())
        self.response_headers.setPlainText(headers_text)
    
    def _on_request_error(self, error: str):
        """Handle request error"""
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send ▶")
        
        self.status_label.setText("Error")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: rgba(239, 68, 68, 0.2);
                color: #ef4444;
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        
        self.response_body.setPlainText(f"Error: {error}")

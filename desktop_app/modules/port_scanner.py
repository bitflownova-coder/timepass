"""
Port Scanner Module - Scan network ports
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QLineEdit,
    QSpinBox, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QBrush
import socket
from typing import List, Tuple, Optional


class ScanThread(QThread):
    """Thread for port scanning"""
    
    progress = pyqtSignal(int)
    port_found = pyqtSignal(int, str, str)  # port, status, service
    finished_scan = pyqtSignal()
    
    # Common ports and services
    COMMON_SERVICES = {
        20: "FTP Data", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
        53: "DNS", 80: "HTTP", 110: "POP3", 119: "NNTP", 123: "NTP",
        143: "IMAP", 161: "SNMP", 194: "IRC", 443: "HTTPS", 445: "SMB",
        465: "SMTPS", 514: "Syslog", 587: "SMTP", 993: "IMAPS", 995: "POP3S",
        1433: "MSSQL", 1521: "Oracle", 3306: "MySQL", 3389: "RDP",
        5432: "PostgreSQL", 5900: "VNC", 6379: "Redis", 8080: "HTTP Alt",
        8443: "HTTPS Alt", 27017: "MongoDB"
    }
    
    def __init__(self, host: str, start_port: int, end_port: int, timeout: float = 0.5):
        super().__init__()
        self.host = host
        self.start_port = start_port
        self.end_port = end_port
        self.timeout = timeout
        self._stop = False
    
    def run(self):
        """Run the scan"""
        total_ports = self.end_port - self.start_port + 1
        
        for i, port in enumerate(range(self.start_port, self.end_port + 1)):
            if self._stop:
                break
            
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                result = sock.connect_ex((self.host, port))
                sock.close()
                
                if result == 0:
                    service = self.COMMON_SERVICES.get(port, "Unknown")
                    self.port_found.emit(port, "Open", service)
            except:
                pass
            
            progress = int((i + 1) / total_ports * 100)
            self.progress.emit(progress)
        
        self.finished_scan.emit()
    
    def stop(self):
        self._stop = True


class PortScannerModule(QWidget):
    """Port Scanner Module"""
    
    COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 5432, 8080]
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        self._scan_thread = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        title = QLabel("🔍 Port Scanner")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f9fafb;
            }
        """)
        layout.addWidget(title)
        
        # Warning
        warning = QLabel("⚠️ Only scan systems you have permission to scan")
        warning.setStyleSheet("""
            QLabel {
                color: #f59e0b;
                background-color: rgba(245, 158, 11, 0.1);
                border: 1px solid #f59e0b;
                border-radius: 6px;
                padding: 8px 12px;
            }
        """)
        layout.addWidget(warning)
        
        # Configuration
        self.config_frame = QFrame(self)
        self.config_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        config_layout = QVBoxLayout(self.config_frame)
        config_layout.setContentsMargins(20, 20, 20, 20)
        config_layout.setSpacing(16)
        
        # Target row
        target_layout = QHBoxLayout()
        
        target_layout.addWidget(QLabel("Target:"))
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("Enter hostname or IP (e.g., localhost, 192.168.1.1)")
        self.host_edit.setText("localhost")
        self.host_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 10px;
                color: #e5e7eb;
            }
        """)
        target_layout.addWidget(self.host_edit, 1)
        
        config_layout.addLayout(target_layout)
        
        # Port range row
        ports_layout = QHBoxLayout()
        
        ports_layout.addWidget(QLabel("Port Range:"))
        
        self.start_port = QSpinBox()
        self.start_port.setRange(1, 65535)
        self.start_port.setValue(1)
        self.start_port.setStyleSheet("""
            QSpinBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
                min-width: 80px;
            }
        """)
        ports_layout.addWidget(self.start_port)
        
        ports_layout.addWidget(QLabel("to"))
        
        self.end_port = QSpinBox()
        self.end_port.setRange(1, 65535)
        self.end_port.setValue(1024)
        self.end_port.setStyleSheet("""
            QSpinBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
                min-width: 80px;
            }
        """)
        ports_layout.addWidget(self.end_port)
        
        # Quick presets
        ports_layout.addWidget(QLabel("Preset:"))
        preset_combo = QComboBox()
        preset_combo.addItems(["Custom", "Common Ports", "Well Known (1-1023)", "All (1-65535)"])
        preset_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
            }
        """)
        preset_combo.currentTextChanged.connect(self._on_preset_changed)
        ports_layout.addWidget(preset_combo)
        
        ports_layout.addStretch()
        
        # Timeout
        ports_layout.addWidget(QLabel("Timeout:"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(100, 5000)
        self.timeout_spin.setValue(500)
        self.timeout_spin.setSuffix(" ms")
        self.timeout_spin.setStyleSheet("""
            QSpinBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
            }
        """)
        ports_layout.addWidget(self.timeout_spin)
        
        config_layout.addLayout(ports_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.scan_btn = QPushButton("🚀 Start Scan")
        self.scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 8px;
                padding: 12px 32px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #374151;
            }
        """)
        self.scan_btn.clicked.connect(self._start_scan)
        btn_layout.addWidget(self.scan_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                border: none;
                border-radius: 8px;
                padding: 12px 32px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
            QPushButton:disabled {
                background-color: #374151;
            }
        """)
        self.stop_btn.clicked.connect(self._stop_scan)
        btn_layout.addWidget(self.stop_btn)
        
        btn_layout.addStretch()
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #374151;
                border-radius: 4px;
                text-align: center;
                color: #e5e7eb;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 4px;
            }
        """)
        btn_layout.addWidget(self.progress_bar, 1)
        
        config_layout.addLayout(btn_layout)
        
        layout.addWidget(self.config_frame)
        
        # Results
        self.results_frame = QFrame(self)
        self.results_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        results_layout = QVBoxLayout(self.results_frame)
        results_layout.setContentsMargins(16, 16, 16, 16)
        
        results_header = QHBoxLayout()
        self.results_label = QLabel("Results")
        self.results_label.setStyleSheet("color: #f9fafb; font-weight: bold;")
        results_header.addWidget(self.results_label)
        results_header.addStretch()
        
        export_btn = QPushButton("📋 Export")
        export_btn.setStyleSheet("""
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
        """)
        export_btn.clicked.connect(self._export_results)
        results_header.addWidget(export_btn)
        
        results_layout.addLayout(results_header)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Port", "Status", "Service"])
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.results_table.setStyleSheet("""
            QTableWidget {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
                gridline-color: #374151;
                color: #e5e7eb;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #374151;
            }
            QHeaderView::section {
                background-color: #1f2937;
                color: #9ca3af;
                border: none;
                padding: 8px;
                font-weight: bold;
            }
        """)
        results_layout.addWidget(self.results_table)
        
        layout.addWidget(self.results_frame, 1)
    
    def _on_preset_changed(self, preset: str):
        """Handle preset change"""
        if preset == "Common Ports":
            self.start_port.setValue(1)
            self.end_port.setValue(1024)
        elif preset == "Well Known (1-1023)":
            self.start_port.setValue(1)
            self.end_port.setValue(1023)
        elif preset == "All (1-65535)":
            self.start_port.setValue(1)
            self.end_port.setValue(65535)
    
    def _start_scan(self):
        """Start port scan"""
        host = self.host_edit.text().strip()
        if not host:
            QMessageBox.warning(self, "Error", "Please enter a target host")
            return
        
        # Validate host
        try:
            socket.gethostbyname(host)
        except socket.gaierror:
            QMessageBox.warning(self, "Error", "Invalid hostname or IP address")
            return
        
        # Clear previous results
        self.results_table.setRowCount(0)
        
        # Update UI
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.results_label.setText("Scanning...")
        
        # Start scan thread
        start = self.start_port.value()
        end = self.end_port.value()
        timeout = self.timeout_spin.value() / 1000.0
        
        self._scan_thread = ScanThread(host, start, end, timeout)
        self._scan_thread.progress.connect(self._on_progress)
        self._scan_thread.port_found.connect(self._on_port_found)
        self._scan_thread.finished_scan.connect(self._on_scan_finished)
        self._scan_thread.start()
    
    def _stop_scan(self):
        """Stop port scan"""
        if self._scan_thread:
            self._scan_thread.stop()
    
    def _on_progress(self, value: int):
        """Update progress"""
        self.progress_bar.setValue(value)
    
    def _on_port_found(self, port: int, status: str, service: str):
        """Handle found port"""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # Port
        port_item = QTableWidgetItem(str(port))
        self.results_table.setItem(row, 0, port_item)
        
        # Status
        status_item = QTableWidgetItem(status)
        status_item.setForeground(QBrush(QColor("#10b981")))
        self.results_table.setItem(row, 1, status_item)
        
        # Service
        self.results_table.setItem(row, 2, QTableWidgetItem(service))
        
        # Update label
        count = self.results_table.rowCount()
        self.results_label.setText(f"Found {count} open port{'s' if count > 1 else ''}")
    
    def _on_scan_finished(self):
        """Handle scan completion"""
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        
        count = self.results_table.rowCount()
        self.results_label.setText(f"Scan Complete - {count} open port{'s' if count != 1 else ''} found")
    
    def _export_results(self):
        """Export results to clipboard"""
        from PyQt6.QtWidgets import QApplication
        
        lines = ["Port\tStatus\tService"]
        for row in range(self.results_table.rowCount()):
            port = self.results_table.item(row, 0).text()
            status = self.results_table.item(row, 1).text()
            service = self.results_table.item(row, 2).text()
            lines.append(f"{port}\t{status}\t{service}")
        
        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(lines))

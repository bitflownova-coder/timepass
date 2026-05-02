"""
Log Viewer Module - View and analyze log files
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QPlainTextEdit,
    QComboBox, QLineEdit, QFileDialog, QListWidget,
    QListWidgetItem, QSplitter, QCheckBox, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer, QFileSystemWatcher
from PyQt6.QtGui import QFont, QColor, QBrush
import re
import os
from datetime import datetime
from typing import List, Optional


class LogViewerModule(QWidget):
    """Log Viewer Module"""
    
    LOG_PATTERNS = {
        "Auto Detect": None,
        "Apache": r'(\d+\.\d+\.\d+\.\d+) .+ \[(.+?)\] "(\w+) (.+?)" (\d+) (\d+|-)',
        "Nginx": r'(\d+\.\d+\.\d+\.\d+) .+ \[(.+?)\] "(\w+) (.+?)" (\d+) (\d+)',
        "Python": r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - (\w+) - (.+)',
        "Java": r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d+)\s+(\w+)\s+.+ - (.+)',
        "Generic": r'^(.+?)\s+(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\s+(.+)$',
    }
    
    LEVEL_COLORS = {
        "DEBUG": "#6b7280",
        "INFO": "#60a5fa",
        "WARN": "#fbbf24",
        "WARNING": "#fbbf24",
        "ERROR": "#f87171",
        "CRITICAL": "#ef4444",
        "FATAL": "#ef4444",
    }
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        self._current_file = None
        self._file_watcher = QFileSystemWatcher()
        self._file_watcher.fileChanged.connect(self._on_file_changed)
        self._tail_mode = False
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📋 Log Viewer")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f9fafb;
            }
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Open file button
        open_btn = QPushButton("📂 Open Log File")
        open_btn.setStyleSheet("""
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
        open_btn.clicked.connect(self._open_file)
        header_layout.addWidget(open_btn)
        
        layout.addLayout(header_layout)
        
        # Current file info
        self.file_label = QLabel("No file loaded")
        self.file_label.setStyleSheet("color: #9ca3af;")
        layout.addWidget(self.file_label)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        
        # Log format
        toolbar.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(list(self.LOG_PATTERNS.keys()))
        self.format_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px 12px;
                color: #e5e7eb;
                min-width: 120px;
            }
        """)
        self.format_combo.currentTextChanged.connect(self._refresh_view)
        toolbar.addWidget(self.format_combo)
        
        # Search
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search logs...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
            }
        """)
        self.search_edit.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.search_edit, 1)
        
        # Level filter
        toolbar.addWidget(QLabel("Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["All", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"])
        self.level_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px 12px;
                color: #e5e7eb;
            }
        """)
        self.level_combo.currentTextChanged.connect(self._refresh_view)
        toolbar.addWidget(self.level_combo)
        
        # Tail mode
        self.tail_check = QCheckBox("Tail Mode")
        self.tail_check.setStyleSheet("color: #e5e7eb;")
        self.tail_check.stateChanged.connect(self._toggle_tail_mode)
        toolbar.addWidget(self.tail_check)
        
        # Refresh
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(36, 36)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                border: none;
                border-radius: 4px;
                color: #e5e7eb;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        refresh_btn.clicked.connect(self._reload_file)
        toolbar.addWidget(refresh_btn)
        
        layout.addLayout(toolbar)
        
        # Main content
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Log table
        self.log_frame = QFrame(self)
        self.log_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        log_layout = QVBoxLayout(self.log_frame)
        log_layout.setContentsMargins(12, 12, 12, 12)
        
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(["Time", "Level", "Source", "Message"])
        self.log_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.log_table.setStyleSheet("""
            QTableWidget {
                background-color: #111827;
                border: none;
                border-radius: 8px;
                gridline-color: #374151;
                color: #e5e7eb;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 6px;
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
        self.log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.log_table.itemClicked.connect(self._on_log_selected)
        log_layout.addWidget(self.log_table)
        
        # Stats bar
        stats_layout = QHBoxLayout()
        
        self.stats_label = QLabel("0 entries")
        self.stats_label.setStyleSheet("color: #9ca3af;")
        stats_layout.addWidget(self.stats_label)
        
        stats_layout.addStretch()
        
        # Level counts
        self.level_counts = {}
        for level in ["DEBUG", "INFO", "WARN", "ERROR"]:
            label = QLabel(f"{level}: 0")
            color = self.LEVEL_COLORS.get(level, "#9ca3af")
            label.setStyleSheet(f"color: {color}; margin-left: 12px;")
            stats_layout.addWidget(label)
            self.level_counts[level] = label
        
        log_layout.addLayout(stats_layout)
        
        splitter.addWidget(self.log_frame)
        
        # Detail view
        self.detail_frame = QFrame(self)
        self.detail_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(12, 12, 12, 12)
        
        detail_header = QHBoxLayout()
        detail_label = QLabel("Log Details")
        detail_label.setStyleSheet("color: #9ca3af; font-weight: bold;")
        detail_header.addWidget(detail_label)
        detail_header.addStretch()
        
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
        copy_btn.clicked.connect(self._copy_detail)
        detail_header.addWidget(copy_btn)
        
        detail_layout.addLayout(detail_header)
        
        self.detail_edit = QPlainTextEdit()
        self.detail_edit.setReadOnly(True)
        self.detail_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #111827;
                border: none;
                border-radius: 8px;
                padding: 12px;
                color: #e5e7eb;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        detail_layout.addWidget(self.detail_edit)
        
        splitter.addWidget(self.detail_frame)
        splitter.setSizes([500, 200])
        
        layout.addWidget(splitter, 1)
        
        # Recent files
        self.recent_frame = QFrame(self)
        self.recent_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 8px;
                border: 1px solid #374151;
            }
        """)
        recent_layout = QHBoxLayout(self.recent_frame)
        recent_layout.setContentsMargins(12, 8, 12, 8)
        
        recent_label = QLabel("Quick Access:")
        recent_label.setStyleSheet("color: #9ca3af;")
        recent_layout.addWidget(recent_label)
        
        # Common log paths
        common_paths = [
            ("Apache", "/var/log/apache2/access.log"),
            ("Nginx", "/var/log/nginx/access.log"),
            ("Syslog", "/var/log/syslog"),
        ]
        
        for name, path in common_paths:
            btn = QPushButton(name)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #374151;
                    border: 1px solid #4b5563;
                    border-radius: 4px;
                    padding: 4px 12px;
                    color: #e5e7eb;
                }
                QPushButton:hover {
                    background-color: #4b5563;
                }
            """)
            btn.clicked.connect(lambda checked, p=path: self._load_file(p))
            recent_layout.addWidget(btn)
        
        recent_layout.addStretch()
        layout.addWidget(self.recent_frame)
    
    def _open_file(self):
        """Open a log file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Log File",
            "",
            "Log Files (*.log *.txt);;All Files (*)"
        )
        
        if file_path:
            self._load_file(file_path)
    
    def _load_file(self, file_path: str):
        """Load a log file"""
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", f"File not found: {file_path}")
            return
        
        # Remove old file from watcher
        if self._current_file and self._current_file in self._file_watcher.files():
            self._file_watcher.removePath(self._current_file)
        
        self._current_file = file_path
        self.file_label.setText(f"📄 {file_path}")
        
        # Add to watcher for tail mode
        if self._tail_mode:
            self._file_watcher.addPath(file_path)
        
        self._reload_file()
    
    def _reload_file(self):
        """Reload current file"""
        if not self._current_file:
            return
        
        try:
            with open(self._current_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            self._parse_logs(lines)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to read file: {e}")
    
    def _parse_logs(self, lines: List[str]):
        """Parse log lines"""
        self.log_table.setRowCount(0)
        
        format_name = self.format_combo.currentText()
        pattern = self.LOG_PATTERNS.get(format_name)
        
        search_text = self.search_edit.text().lower()
        level_filter = self.level_combo.currentText()
        
        counts = {"DEBUG": 0, "INFO": 0, "WARN": 0, "ERROR": 0}
        filtered_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to parse
            time_str = ""
            level = "INFO"
            source = ""
            message = line
            
            if pattern:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    if len(groups) >= 3:
                        time_str = groups[0]
                        level = groups[1].upper()
                        message = groups[2] if len(groups) > 2 else line
            else:
                # Auto-detect
                for p in self.LOG_PATTERNS.values():
                    if p:
                        match = re.match(p, line)
                        if match:
                            groups = match.groups()
                            if len(groups) >= 2:
                                time_str = groups[0]
                                level = groups[1].upper() if len(groups) > 1 else "INFO"
                                message = groups[2] if len(groups) > 2 else line
                            break
            
            # Normalize level
            if level == "WARNING":
                level = "WARN"
            if level not in counts:
                level = "INFO"
            
            counts[level] = counts.get(level, 0) + 1
            
            # Apply filters
            if level_filter != "All" and level != level_filter:
                continue
            
            if search_text and search_text not in line.lower():
                continue
            
            filtered_count += 1
            
            # Add to table
            row = self.log_table.rowCount()
            self.log_table.insertRow(row)
            
            # Time
            time_item = QTableWidgetItem(time_str)
            time_item.setData(Qt.ItemDataRole.UserRole, line)
            self.log_table.setItem(row, 0, time_item)
            
            # Level with color
            level_item = QTableWidgetItem(level)
            color = QColor(self.LEVEL_COLORS.get(level, "#9ca3af"))
            level_item.setForeground(QBrush(color))
            self.log_table.setItem(row, 1, level_item)
            
            # Source
            self.log_table.setItem(row, 2, QTableWidgetItem(source))
            
            # Message (truncated)
            msg_display = message[:200] + "..." if len(message) > 200 else message
            self.log_table.setItem(row, 3, QTableWidgetItem(msg_display))
        
        # Update stats
        total = sum(counts.values())
        self.stats_label.setText(f"{filtered_count} of {total} entries")
        
        for level, label in self.level_counts.items():
            label.setText(f"{level}: {counts.get(level, 0)}")
        
        # Scroll to bottom if tail mode
        if self._tail_mode:
            self.log_table.scrollToBottom()
    
    def _on_log_selected(self, item: QTableWidgetItem):
        """Handle log line selection"""
        row = item.row()
        time_item = self.log_table.item(row, 0)
        if time_item:
            full_line = time_item.data(Qt.ItemDataRole.UserRole)
            self.detail_edit.setPlainText(full_line)
    
    def _on_search_changed(self, text: str):
        """Handle search text change"""
        self._reload_file()
    
    def _refresh_view(self):
        """Refresh the view"""
        self._reload_file()
    
    def _toggle_tail_mode(self, state: int):
        """Toggle tail mode"""
        self._tail_mode = state == Qt.CheckState.Checked.value
        
        if self._current_file:
            if self._tail_mode:
                self._file_watcher.addPath(self._current_file)
            else:
                if self._current_file in self._file_watcher.files():
                    self._file_watcher.removePath(self._current_file)
    
    def _on_file_changed(self, path: str):
        """Handle file change in tail mode"""
        if path == self._current_file and self._tail_mode:
            self._reload_file()
    
    def _copy_detail(self):
        """Copy detail to clipboard"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.detail_edit.toPlainText())

"""
Regex Tester Module - Test and debug regular expressions
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QPlainTextEdit,
    QComboBox, QCheckBox, QLineEdit, QListWidget,
    QListWidgetItem, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor, QBrush
import re
from typing import List, Tuple


class RegexTesterModule(QWidget):
    """Regex Tester Module"""
    
    # Common regex patterns library
    PATTERN_LIBRARY = {
        "Email": r"[\w\.-]+@[\w\.-]+\.\w+",
        "URL": r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
        "IP Address (IPv4)": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "Phone (US)": r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        "Date (YYYY-MM-DD)": r"\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])",
        "Date (MM/DD/YYYY)": r"(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])/\d{4}",
        "Time (HH:MM)": r"(?:[01]\d|2[0-3]):[0-5]\d",
        "Credit Card": r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}",
        "Hex Color": r"#(?:[0-9a-fA-F]{3}){1,2}\b",
        "HTML Tag": r"<([a-z]+)([^<]+)*(?:>(.*)<\/\1>|\s+\/>)",
        "UUID": r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "MAC Address": r"(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}",
        "SSN": r"\d{3}-\d{2}-\d{4}",
        "ZIP Code (US)": r"\d{5}(?:-\d{4})?",
        "Slug": r"[a-z0-9]+(?:-[a-z0-9]+)*",
        "Username": r"[a-zA-Z][a-zA-Z0-9_]{2,15}",
        "Password (Strong)": r"(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}",
        "File Path (Windows)": r"[a-zA-Z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n]*",
        "File Path (Unix)": r"(?:/[^/\0]+)+/?",
        "JSON Key": r'"([^"]+)"\s*:',
        "Whitespace": r"\s+",
        "Integer": r"-?\d+",
        "Float": r"-?\d+\.\d+",
        "Word": r"\b\w+\b",
    }
    
    MATCH_COLORS = [
        "#f87171", "#fb923c", "#facc15", "#4ade80", 
        "#22d3ee", "#818cf8", "#e879f9", "#fb7185"
    ]
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._do_match)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        title = QLabel("🔍 Regex Tester")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f9fafb;
            }
        """)
        layout.addWidget(title)
        
        # Pattern input area
        self.pattern_frame = QFrame(self)
        self.pattern_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        pattern_layout = QVBoxLayout(self.pattern_frame)
        pattern_layout.setContentsMargins(16, 16, 16, 16)
        
        # Pattern row
        pattern_row = QHBoxLayout()
        
        pattern_label = QLabel("Pattern:")
        pattern_label.setStyleSheet("color: #9ca3af; font-weight: bold;")
        pattern_row.addWidget(pattern_label)
        
        self.pattern_edit = QLineEdit()
        self.pattern_edit.setPlaceholderText("Enter your regex pattern...")
        self.pattern_edit.setStyleSheet("""
            QLineEdit {
                background-color: #111827;
                border: 2px solid #4b5563;
                border-radius: 8px;
                padding: 12px;
                color: #f9fafb;
                font-family: 'Consolas', monospace;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #6366f1;
            }
        """)
        self.pattern_edit.textChanged.connect(self._on_pattern_changed)
        pattern_row.addWidget(self.pattern_edit, 1)
        
        # Pattern library
        self.library_combo = QComboBox()
        self.library_combo.addItem("📚 Pattern Library")
        for name in self.PATTERN_LIBRARY.keys():
            self.library_combo.addItem(name)
        self.library_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 8px 16px;
                color: #e5e7eb;
                min-width: 160px;
            }
        """)
        self.library_combo.currentTextChanged.connect(self._on_library_selected)
        pattern_row.addWidget(self.library_combo)
        
        pattern_layout.addLayout(pattern_row)
        
        # Options row
        options_row = QHBoxLayout()
        
        self.case_insensitive = QCheckBox("Case Insensitive (i)")
        self.case_insensitive.setStyleSheet("color: #9ca3af;")
        self.case_insensitive.stateChanged.connect(self._trigger_match)
        options_row.addWidget(self.case_insensitive)
        
        self.multiline = QCheckBox("Multiline (m)")
        self.multiline.setStyleSheet("color: #9ca3af;")
        self.multiline.stateChanged.connect(self._trigger_match)
        options_row.addWidget(self.multiline)
        
        self.dotall = QCheckBox("Dot All (s)")
        self.dotall.setStyleSheet("color: #9ca3af;")
        self.dotall.stateChanged.connect(self._trigger_match)
        options_row.addWidget(self.dotall)
        
        self.global_match = QCheckBox("Global (g)")
        self.global_match.setChecked(True)
        self.global_match.setStyleSheet("color: #9ca3af;")
        self.global_match.stateChanged.connect(self._trigger_match)
        options_row.addWidget(self.global_match)
        
        options_row.addStretch()
        
        # Status
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #9ca3af;")
        options_row.addWidget(self.status_label)
        
        pattern_layout.addLayout(options_row)
        
        layout.addWidget(self.pattern_frame)
        
        # Main content area
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Test string input
        self.test_frame = QFrame(self)
        self.test_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        test_layout = QVBoxLayout(self.test_frame)
        test_layout.setContentsMargins(16, 16, 16, 16)
        
        test_header = QHBoxLayout()
        test_label = QLabel("Test String:")
        test_label.setStyleSheet("color: #9ca3af; font-weight: bold;")
        test_header.addWidget(test_label)
        test_header.addStretch()
        
        sample_btn = QPushButton("📝 Sample Text")
        sample_btn.setStyleSheet("""
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
        sample_btn.clicked.connect(self._insert_sample)
        test_header.addWidget(sample_btn)
        
        test_layout.addLayout(test_header)
        
        self.test_edit = QTextEdit()
        self.test_edit.setPlaceholderText("Enter text to test against...")
        self.test_edit.setStyleSheet("""
            QTextEdit {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
                color: #e5e7eb;
                font-family: 'Consolas', monospace;
                font-size: 13px;
            }
        """)
        self.test_edit.textChanged.connect(self._trigger_match)
        test_layout.addWidget(self.test_edit)
        
        splitter.addWidget(self.test_frame)
        
        # Results area
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
        
        results_label = QLabel("Matches:")
        results_label.setStyleSheet("color: #9ca3af; font-weight: bold;")
        results_layout.addWidget(results_label)
        
        # Match table
        self.match_table = QTableWidget()
        self.match_table.setColumnCount(5)
        self.match_table.setHorizontalHeaderLabels(["#", "Match", "Groups", "Start", "End"])
        self.match_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.match_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.match_table.setStyleSheet("""
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
        self.match_table.itemClicked.connect(self._on_match_clicked)
        results_layout.addWidget(self.match_table)
        
        splitter.addWidget(self.results_frame)
        splitter.setSizes([400, 300])
        
        layout.addWidget(splitter, 1)
        
        # Replacement section
        self.replace_frame = QFrame(self)
        self.replace_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 8px;
                border: 1px solid #374151;
            }
        """)
        replace_layout = QHBoxLayout(self.replace_frame)
        replace_layout.setContentsMargins(16, 12, 16, 12)
        
        replace_label = QLabel("Replace:")
        replace_label.setStyleSheet("color: #9ca3af;")
        replace_layout.addWidget(replace_label)
        
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("Replacement string (use $1, $2 for groups)...")
        self.replace_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
                font-family: 'Consolas', monospace;
            }
        """)
        replace_layout.addWidget(self.replace_edit, 1)
        
        replace_btn = QPushButton("Replace All")
        replace_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: #818cf8;
            }
        """)
        replace_btn.clicked.connect(self._do_replace)
        replace_layout.addWidget(replace_btn)
        
        copy_result_btn = QPushButton("📋 Copy Result")
        copy_result_btn.setStyleSheet("""
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
        """)
        copy_result_btn.clicked.connect(self._copy_result)
        replace_layout.addWidget(copy_result_btn)
        
        layout.addWidget(self.replace_frame)
    
    def _on_pattern_changed(self, text: str):
        """Handle pattern change with debouncing"""
        self._trigger_match()
    
    def _on_library_selected(self, name: str):
        """Handle pattern library selection"""
        if name in self.PATTERN_LIBRARY:
            self.pattern_edit.setText(self.PATTERN_LIBRARY[name])
    
    def _trigger_match(self):
        """Trigger match with debounce"""
        self._debounce_timer.stop()
        self._debounce_timer.start(250)
    
    def _do_match(self):
        """Execute regex matching"""
        pattern_text = self.pattern_edit.text()
        test_text = self.test_edit.toPlainText()
        
        self.match_table.setRowCount(0)
        
        if not pattern_text:
            self._update_status("Enter a pattern", "#9ca3af")
            self._clear_highlights()
            return
        
        # Build flags
        flags = 0
        if self.case_insensitive.isChecked():
            flags |= re.IGNORECASE
        if self.multiline.isChecked():
            flags |= re.MULTILINE
        if self.dotall.isChecked():
            flags |= re.DOTALL
        
        try:
            pattern = re.compile(pattern_text, flags)
            
            if self.global_match.isChecked():
                matches = list(pattern.finditer(test_text))
            else:
                match = pattern.search(test_text)
                matches = [match] if match else []
            
            # Update status
            if matches:
                self._update_status(f"✓ {len(matches)} match{'es' if len(matches) > 1 else ''} found", "#10b981")
            else:
                self._update_status("No matches found", "#f59e0b")
            
            # Populate table
            for i, m in enumerate(matches):
                row = self.match_table.rowCount()
                self.match_table.insertRow(row)
                
                # Index
                item = QTableWidgetItem(str(i + 1))
                item.setData(Qt.ItemDataRole.UserRole, (m.start(), m.end()))
                color = QColor(self.MATCH_COLORS[i % len(self.MATCH_COLORS)])
                item.setForeground(QBrush(color))
                self.match_table.setItem(row, 0, item)
                
                # Match text
                match_item = QTableWidgetItem(m.group(0))
                match_item.setForeground(QBrush(color))
                self.match_table.setItem(row, 1, match_item)
                
                # Groups
                if m.groups():
                    groups_text = ", ".join(f"${i+1}: {g}" for i, g in enumerate(m.groups()) if g)
                    self.match_table.setItem(row, 2, QTableWidgetItem(groups_text))
                else:
                    self.match_table.setItem(row, 2, QTableWidgetItem("-"))
                
                # Positions
                self.match_table.setItem(row, 3, QTableWidgetItem(str(m.start())))
                self.match_table.setItem(row, 4, QTableWidgetItem(str(m.end())))
            
            # Highlight matches
            self._highlight_matches(matches)
            
        except re.error as e:
            self._update_status(f"✗ Invalid pattern: {e}", "#ef4444")
            self._clear_highlights()
    
    def _highlight_matches(self, matches: List):
        """Highlight matches in test text"""
        cursor = self.test_edit.textCursor()
        
        # Clear existing formatting
        cursor.select(QTextCursor.SelectionType.Document)
        default_fmt = QTextCharFormat()
        default_fmt.setBackground(QColor("transparent"))
        cursor.setCharFormat(default_fmt)
        
        # Highlight each match
        for i, m in enumerate(matches):
            cursor.setPosition(m.start())
            cursor.setPosition(m.end(), QTextCursor.MoveMode.KeepAnchor)
            
            fmt = QTextCharFormat()
            color = QColor(self.MATCH_COLORS[i % len(self.MATCH_COLORS)])
            color.setAlpha(80)
            fmt.setBackground(color)
            cursor.setCharFormat(fmt)
    
    def _clear_highlights(self):
        """Clear all highlights"""
        cursor = self.test_edit.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("transparent"))
        cursor.setCharFormat(fmt)
    
    def _on_match_clicked(self, item: QTableWidgetItem):
        """Handle match table click - highlight in text"""
        row = item.row()
        first_item = self.match_table.item(row, 0)
        if first_item:
            pos_data = first_item.data(Qt.ItemDataRole.UserRole)
            if pos_data:
                start, end = pos_data
                cursor = self.test_edit.textCursor()
                cursor.setPosition(start)
                cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
                self.test_edit.setTextCursor(cursor)
                self.test_edit.setFocus()
    
    def _do_replace(self):
        """Perform replacement"""
        pattern_text = self.pattern_edit.text()
        test_text = self.test_edit.toPlainText()
        replace_text = self.replace_edit.text()
        
        if not pattern_text:
            return
        
        # Build flags
        flags = 0
        if self.case_insensitive.isChecked():
            flags |= re.IGNORECASE
        if self.multiline.isChecked():
            flags |= re.MULTILINE
        if self.dotall.isChecked():
            flags |= re.DOTALL
        
        try:
            # Convert $1, $2 to Python \1, \2
            py_replace = re.sub(r'\$(\d+)', r'\\\1', replace_text)
            
            pattern = re.compile(pattern_text, flags)
            
            if self.global_match.isChecked():
                result, count = pattern.subn(py_replace, test_text)
            else:
                result, count = pattern.subn(py_replace, test_text, count=1)
            
            self.test_edit.setPlainText(result)
            self._update_status(f"✓ {count} replacement{'s' if count > 1 else ''} made", "#10b981")
            
        except re.error as e:
            self._update_status(f"✗ Replace error: {e}", "#ef4444")
    
    def _insert_sample(self):
        """Insert sample text"""
        sample = """Hello World! My email is john.doe@example.com
Another email: jane_smith@company.org

Phone numbers: (555) 123-4567, 555.987.6543

URLs:
https://www.example.com/path/to/page
http://subdomain.domain.co.uk/path?query=value

Dates: 2024-01-15, 12/25/2023
Times: 09:30, 14:45, 23:59

IP Addresses: 192.168.1.1, 10.0.0.255

Colors: #FF5733, #333, #A0B1C2

UUIDs: 550e8400-e29b-41d4-a716-446655440000

Some code: var myVar = "Hello"; const x = 42;"""
        self.test_edit.setPlainText(sample)
    
    def _copy_result(self):
        """Copy current text to clipboard"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.test_edit.toPlainText())
        self._update_status("✓ Copied to clipboard", "#10b981")
    
    def _update_status(self, message: str, color: str):
        """Update status label"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color};")

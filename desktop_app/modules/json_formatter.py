"""
JSON/XML Formatter Module - Format, validate, and transform data
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QPlainTextEdit,
    QComboBox, QTabWidget, QSplitter, QTextEdit,
    QMessageBox, QCheckBox, QSpinBox, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat
from typing import Any, Optional
import json
import re

try:
    import xmltodict
    HAS_XML = True
except ImportError:
    HAS_XML = False


class JsonHighlighter(QSyntaxHighlighter):
    """JSON syntax highlighter"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []
        
        # Keys
        key_format = QTextCharFormat()
        key_format.setForeground(QColor("#82aaff"))
        self._rules.append((re.compile(r'"[^"]*"\s*:'), key_format))
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#c3e88d"))
        self._rules.append((re.compile(r':\s*"[^"]*"'), string_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#f78c6c"))
        self._rules.append((re.compile(r'\b-?\d+\.?\d*\b'), number_format))
        
        # Booleans and null
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#c792ea"))
        self._rules.append((re.compile(r'\b(true|false|null)\b'), keyword_format))
        
        # Brackets
        bracket_format = QTextCharFormat()
        bracket_format.setForeground(QColor("#89ddff"))
        self._rules.append((re.compile(r'[\[\]{}]'), bracket_format))
    
    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class JsonFormatterModule(QWidget):
    """JSON/XML Formatter Module"""
    
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
        header_layout = QHBoxLayout()
        
        title = QLabel("📋 JSON / XML Formatter")
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
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Format selector
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JSON", "XML"])
        self.format_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 8px 16px;
                color: #e5e7eb;
                min-width: 100px;
            }
        """)
        toolbar.addWidget(QLabel("Format:"))
        toolbar.addWidget(self.format_combo)
        
        # Indent size
        toolbar.addWidget(QLabel("Indent:"))
        self.indent_spin = QSpinBox()
        self.indent_spin.setRange(1, 8)
        self.indent_spin.setValue(2)
        self.indent_spin.setStyleSheet("""
            QSpinBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px;
                color: #e5e7eb;
            }
        """)
        toolbar.addWidget(self.indent_spin)
        
        toolbar.addStretch()
        
        # Action buttons
        format_btn = QPushButton("✨ Format")
        format_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        format_btn.clicked.connect(self._format_input)
        toolbar.addWidget(format_btn)
        
        minify_btn = QPushButton("📦 Minify")
        minify_btn.setStyleSheet("""
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
        """)
        minify_btn.clicked.connect(self._minify_input)
        toolbar.addWidget(minify_btn)
        
        validate_btn = QPushButton("✓ Validate")
        validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #d97706;
            }
        """)
        validate_btn.clicked.connect(self._validate_input)
        toolbar.addWidget(validate_btn)
        
        convert_btn = QPushButton("🔄 Convert")
        convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }
        """)
        convert_btn.clicked.connect(self._convert_format)
        toolbar.addWidget(convert_btn)
        
        layout.addLayout(toolbar)
        
        # Editor
        self.editor_frame = QFrame(self)
        self.editor_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        editor_layout = QVBoxLayout(self.editor_frame)
        editor_layout.setContentsMargins(16, 16, 16, 16)
        
        # Splitter for input/output
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Input panel
        self.input_panel = QFrame(self)
        input_layout = QVBoxLayout(self.input_panel)
        input_layout.setContentsMargins(0, 0, 8, 0)
        
        input_header = QHBoxLayout()
        input_label = QLabel("Input")
        input_label.setStyleSheet("color: #9ca3af; font-weight: bold;")
        input_header.addWidget(input_label)
        input_header.addStretch()
        
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
        paste_btn.clicked.connect(self._paste_input)
        input_header.addWidget(paste_btn)
        
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
        clear_btn.clicked.connect(lambda: self.input_edit.clear())
        input_header.addWidget(clear_btn)
        
        input_layout.addLayout(input_header)
        
        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText("Paste your JSON or XML here...")
        self.input_edit.setStyleSheet("""
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
        self._input_highlighter = JsonHighlighter(self.input_edit.document())
        input_layout.addWidget(self.input_edit)
        
        splitter.addWidget(self.input_panel)
        
        # Output panel
        self.output_panel = QFrame(self)
        output_layout = QVBoxLayout(self.output_panel)
        output_layout.setContentsMargins(8, 0, 0, 0)
        
        output_header = QHBoxLayout()
        output_label = QLabel("Output")
        output_label.setStyleSheet("color: #9ca3af; font-weight: bold;")
        output_header.addWidget(output_label)
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
        copy_btn.clicked.connect(self._copy_output)
        output_header.addWidget(copy_btn)
        
        output_layout.addLayout(output_header)
        
        self.output_edit = QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("Formatted output will appear here...")
        self.output_edit.setStyleSheet("""
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
        self._output_highlighter = JsonHighlighter(self.output_edit.document())
        output_layout.addWidget(self.output_edit)
        
        splitter.addWidget(self.output_panel)
        splitter.setSizes([500, 500])
        
        editor_layout.addWidget(splitter)
        
        # Status bar
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            QLabel {
                color: #9ca3af;
                font-size: 12px;
                padding: 4px;
            }
        """)
        editor_layout.addWidget(self.status_label)
        
        layout.addWidget(self.editor_frame, 1)
        
        # JSONPath query section
        self.query_frame = QFrame(self)
        self.query_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 8px;
                border: 1px solid #374151;
            }
        """)
        query_layout = QHBoxLayout(self.query_frame)
        query_layout.setContentsMargins(12, 12, 12, 12)
        
        query_label = QLabel("JSONPath Query:")
        query_label.setStyleSheet("color: #9ca3af;")
        query_layout.addWidget(query_label)
        
        self.query_edit = QLineEdit()
        self.query_edit.setPlaceholderText("$.store.book[0].title")
        self.query_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
                font-family: 'Consolas', monospace;
            }
        """)
        query_layout.addWidget(self.query_edit, 1)
        
        query_btn = QPushButton("Query")
        query_btn.setStyleSheet("""
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
        query_btn.clicked.connect(self._run_query)
        query_layout.addWidget(query_btn)
        
        layout.addWidget(self.query_frame)
    
    def _format_input(self):
        """Format the input"""
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        
        fmt = self.format_combo.currentText()
        indent = self.indent_spin.value()
        
        try:
            if fmt == "JSON":
                data = json.loads(text)
                formatted = json.dumps(data, indent=indent, ensure_ascii=False)
                self.output_edit.setPlainText(formatted)
                self._set_status("✓ JSON formatted successfully", "#10b981")
            else:
                if HAS_XML:
                    # Try to parse and reformat XML
                    data = xmltodict.parse(text)
                    formatted = xmltodict.unparse(data, pretty=True)
                    self.output_edit.setPlainText(formatted)
                    self._set_status("✓ XML formatted successfully", "#10b981")
                else:
                    self._set_status("✗ XML support not installed (pip install xmltodict)", "#ef4444")
        except json.JSONDecodeError as e:
            self._set_status(f"✗ JSON Error: {e}", "#ef4444")
        except Exception as e:
            self._set_status(f"✗ Error: {e}", "#ef4444")
    
    def _minify_input(self):
        """Minify the input"""
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        
        fmt = self.format_combo.currentText()
        
        try:
            if fmt == "JSON":
                data = json.loads(text)
                minified = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
                self.output_edit.setPlainText(minified)
                self._set_status(f"✓ Minified: {len(text)} → {len(minified)} chars", "#10b981")
            else:
                if HAS_XML:
                    data = xmltodict.parse(text)
                    minified = xmltodict.unparse(data, pretty=False)
                    self.output_edit.setPlainText(minified)
                    self._set_status(f"✓ Minified: {len(text)} → {len(minified)} chars", "#10b981")
                else:
                    self._set_status("✗ XML support not installed", "#ef4444")
        except Exception as e:
            self._set_status(f"✗ Error: {e}", "#ef4444")
    
    def _validate_input(self):
        """Validate the input"""
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        
        fmt = self.format_combo.currentText()
        
        try:
            if fmt == "JSON":
                data = json.loads(text)
                item_count = self._count_items(data)
                self._set_status(f"✓ Valid JSON ({item_count} items)", "#10b981")
            else:
                if HAS_XML:
                    xmltodict.parse(text)
                    self._set_status("✓ Valid XML", "#10b981")
                else:
                    self._set_status("✗ XML support not installed", "#ef4444")
        except json.JSONDecodeError as e:
            self._set_status(f"✗ Invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}", "#ef4444")
        except Exception as e:
            self._set_status(f"✗ Invalid: {e}", "#ef4444")
    
    def _convert_format(self):
        """Convert between JSON and XML"""
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        
        if not HAS_XML:
            self._set_status("✗ XML support not installed (pip install xmltodict)", "#ef4444")
            return
        
        fmt = self.format_combo.currentText()
        
        try:
            if fmt == "JSON":
                # Convert JSON to XML
                data = json.loads(text)
                # Wrap in root if needed
                if not isinstance(data, dict) or len(data) != 1:
                    data = {"root": data}
                xml = xmltodict.unparse(data, pretty=True)
                self.output_edit.setPlainText(xml)
                self.format_combo.setCurrentText("XML")
                self._set_status("✓ Converted JSON → XML", "#10b981")
            else:
                # Convert XML to JSON
                data = xmltodict.parse(text)
                output = json.dumps(data, indent=2, ensure_ascii=False)
                self.output_edit.setPlainText(output)
                self.format_combo.setCurrentText("JSON")
                self._set_status("✓ Converted XML → JSON", "#10b981")
        except Exception as e:
            self._set_status(f"✗ Conversion error: {e}", "#ef4444")
    
    def _run_query(self):
        """Run JSONPath query"""
        text = self.input_edit.toPlainText().strip()
        query = self.query_edit.text().strip()
        
        if not text or not query:
            return
        
        try:
            data = json.loads(text)
            
            # Simple JSONPath implementation
            result = self._jsonpath_query(data, query)
            
            if result is None:
                self.output_edit.setPlainText("null")
            elif isinstance(result, (dict, list)):
                self.output_edit.setPlainText(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                self.output_edit.setPlainText(str(result))
            
            self._set_status("✓ Query executed", "#10b981")
        except Exception as e:
            self._set_status(f"✗ Query error: {e}", "#ef4444")
    
    def _jsonpath_query(self, data: Any, path: str) -> Any:
        """Simple JSONPath query implementation"""
        # Remove leading $
        if path.startswith("$"):
            path = path[1:]
        if path.startswith("."):
            path = path[1:]
        
        if not path:
            return data
        
        result = data
        # Split on dots but respect brackets
        parts = re.split(r'\.(?![^\[]*\])', path)
        
        for part in parts:
            if not part:
                continue
            
            # Handle array indexing
            match = re.match(r'(\w*)(?:\[(\d+)\])?', part)
            if match:
                key, index = match.groups()
                
                if key:
                    if isinstance(result, dict):
                        result = result.get(key)
                    else:
                        return None
                
                if index is not None and result is not None:
                    idx = int(index)
                    if isinstance(result, list) and 0 <= idx < len(result):
                        result = result[idx]
                    else:
                        return None
        
        return result
    
    def _count_items(self, data: Any) -> int:
        """Count items in data structure"""
        if isinstance(data, dict):
            return sum(self._count_items(v) for v in data.values()) + len(data)
        elif isinstance(data, list):
            return sum(self._count_items(item) for item in data) + len(data)
        return 1
    
    def _paste_input(self):
        """Paste from clipboard"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        self.input_edit.setPlainText(clipboard.text())
    
    def _copy_output(self):
        """Copy output to clipboard"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.output_edit.toPlainText())
        self._set_status("✓ Copied to clipboard", "#10b981")
    
    def _set_status(self, message: str, color: str):
        """Set status message"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 12px;
                padding: 4px;
            }}
        """)

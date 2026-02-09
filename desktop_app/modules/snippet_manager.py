"""
Snippet Manager Module - Personal code snippet library
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QLineEdit, QTextEdit,
    QListWidget, QListWidgetItem, QSplitter, QComboBox,
    QDialog, QFormLayout, QMessageBox, QTreeWidget,
    QTreeWidgetItem, QPlainTextEdit, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat
from datetime import datetime
from typing import Optional, List, Dict
import re

from core.database import CodeSnippet, SnippetCategory, get_session


class CodeHighlighter(QSyntaxHighlighter):
    """Multi-language syntax highlighter"""
    
    LANGUAGES = {
        "python": {
            "keywords": ["def", "class", "import", "from", "return", "if", "else", "elif",
                        "for", "while", "try", "except", "finally", "with", "as", "yield",
                        "lambda", "pass", "break", "continue", "True", "False", "None",
                        "and", "or", "not", "in", "is", "async", "await"],
            "keyword_color": "#c792ea",
            "string_color": "#c3e88d",
            "comment": "#",
            "comment_color": "#676e95",
            "number_color": "#f78c6c"
        },
        "kotlin": {
            "keywords": ["fun", "val", "var", "class", "object", "interface", "return",
                        "if", "else", "when", "for", "while", "do", "try", "catch",
                        "finally", "throw", "import", "package", "private", "public",
                        "override", "suspend", "data", "sealed", "companion", "null",
                        "true", "false", "this", "super"],
            "keyword_color": "#c792ea",
            "string_color": "#c3e88d",
            "comment": "//",
            "comment_color": "#676e95",
            "number_color": "#f78c6c"
        },
        "javascript": {
            "keywords": ["function", "const", "let", "var", "return", "if", "else",
                        "for", "while", "do", "switch", "case", "break", "continue",
                        "try", "catch", "finally", "throw", "class", "extends",
                        "import", "export", "from", "async", "await", "new", "this",
                        "true", "false", "null", "undefined"],
            "keyword_color": "#c792ea",
            "string_color": "#c3e88d",
            "comment": "//",
            "comment_color": "#676e95",
            "number_color": "#f78c6c"
        },
        "sql": {
            "keywords": ["SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE",
                        "CREATE", "ALTER", "DROP", "TABLE", "INDEX", "VIEW",
                        "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "ON", "AND",
                        "OR", "NOT", "IN", "LIKE", "ORDER", "BY", "GROUP", "HAVING",
                        "LIMIT", "OFFSET", "AS", "NULL", "PRIMARY", "KEY", "FOREIGN"],
            "keyword_color": "#82aaff",
            "string_color": "#c3e88d",
            "comment": "--",
            "comment_color": "#676e95",
            "number_color": "#f78c6c"
        }
    }
    
    def __init__(self, language: str = "python", parent=None):
        super().__init__(parent)
        self._rules = []
        self.set_language(language)
    
    def set_language(self, language: str):
        """Set the language for highlighting"""
        self._rules = []
        
        lang_config = self.LANGUAGES.get(language.lower(), self.LANGUAGES["python"])
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(lang_config["keyword_color"]))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        keywords = lang_config["keywords"]
        keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
        self._rules.append((re.compile(keyword_pattern, re.IGNORECASE), keyword_format))
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(lang_config["string_color"]))
        self._rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self._rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(lang_config["number_color"]))
        self._rules.append((re.compile(r'\b\d+\.?\d*\b'), number_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(lang_config["comment_color"]))
        comment_format.setFontItalic(True)
        comment_char = lang_config["comment"]
        self._rules.append((re.compile(f'{re.escape(comment_char)}.*$', re.MULTILINE), comment_format))
        
        self.rehighlight()
    
    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class SnippetDialog(QDialog):
    """Dialog to add/edit a snippet"""
    
    def __init__(self, snippet: Optional[CodeSnippet] = None, 
                 categories: List[SnippetCategory] = None, parent=None):
        super().__init__(parent)
        self.snippet = snippet
        self.categories = categories or []
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Add Snippet" if not self.snippet else "Edit Snippet")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #1f2937;
            }
            QLabel {
                color: #e5e7eb;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
            }
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
            QPushButton#cancelBtn {
                background-color: #374151;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Snippet title")
        form.addRow("Title:", self.title_edit)
        
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Brief description")
        form.addRow("Description:", self.desc_edit)
        
        # Language selector
        self.lang_combo = QComboBox()
        self.lang_combo.addItems([
            "Python", "Kotlin", "JavaScript", "TypeScript", "Java",
            "SQL", "HTML", "CSS", "JSON", "XML", "Bash", "PowerShell",
            "YAML", "Markdown", "Plaintext"
        ])
        self.lang_combo.currentTextChanged.connect(self._on_language_changed)
        form.addRow("Language:", self.lang_combo)
        
        # Category selector
        self.category_combo = QComboBox()
        self.category_combo.addItem("No Category", None)
        for cat in self.categories:
            self.category_combo.addItem(cat.name, cat.id)
        form.addRow("Category:", self.category_combo)
        
        layout.addLayout(form)
        
        # Code editor
        code_label = QLabel("Code:")
        layout.addWidget(code_label)
        
        self.code_edit = QPlainTextEdit()
        self.code_edit.setPlaceholderText("Paste your code here...")
        self.code_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
                color: #e5e7eb;
                font-family: 'Consolas', 'Fira Code', monospace;
                font-size: 13px;
            }
        """)
        self._highlighter = CodeHighlighter("python", self.code_edit.document())
        layout.addWidget(self.code_edit, 1)
        
        # Tags
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("tag1, tag2, tag3")
        form2 = QFormLayout()
        form2.addRow("Tags:", self.tags_edit)
        layout.addLayout(form2)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Snippet")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        # Load existing data
        if self.snippet:
            self.title_edit.setText(self.snippet.title)
            self.desc_edit.setText(self.snippet.description or "")
            self.code_edit.setPlainText(self.snippet.code)
            self.tags_edit.setText(", ".join(self.snippet.tags or []))
            
            idx = self.lang_combo.findText(self.snippet.language, Qt.MatchFlag.MatchFixedString)
            if idx >= 0:
                self.lang_combo.setCurrentIndex(idx)
            
            if self.snippet.category_id:
                idx = self.category_combo.findData(self.snippet.category_id)
                if idx >= 0:
                    self.category_combo.setCurrentIndex(idx)
    
    def _on_language_changed(self, language: str):
        """Update highlighter when language changes"""
        self._highlighter.set_language(language.lower())
    
    def _save(self):
        title = self.title_edit.text().strip()
        code = self.code_edit.toPlainText().strip()
        
        if not title:
            QMessageBox.warning(self, "Validation", "Please enter a title.")
            return
        
        if not code:
            QMessageBox.warning(self, "Validation", "Please enter some code.")
            return
        
        session = get_session()
        
        if self.snippet:
            snippet = session.query(CodeSnippet).get(self.snippet.id)
        else:
            snippet = CodeSnippet()
            session.add(snippet)
        
        snippet.title = title
        snippet.description = self.desc_edit.text().strip() or None
        snippet.code = code
        snippet.language = self.lang_combo.currentText().lower()
        snippet.category_id = self.category_combo.currentData()
        snippet.tags = [t.strip() for t in self.tags_edit.text().split(",") if t.strip()]
        
        session.commit()
        session.close()
        
        self.accept()


class SnippetManagerModule(QWidget):
    """Snippet Manager Module"""
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        self._current_snippet: Optional[CodeSnippet] = None
        self._setup_ui()
        self._load_snippets()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("💻 Code Snippets")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f9fafb;
            }
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Search
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search snippets...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 8px 12px;
                color: #e5e7eb;
                min-width: 250px;
            }
        """)
        self.search_edit.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_edit)
        
        # New snippet button
        new_btn = QPushButton("+ New Snippet")
        new_btn.setStyleSheet("""
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
        new_btn.clicked.connect(self._new_snippet)
        header_layout.addWidget(new_btn)
        
        layout.addLayout(header_layout)
        
        # Main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Snippet list
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        
        # Filter by language
        filter_layout = QHBoxLayout()
        self.lang_filter = QComboBox()
        self.lang_filter.addItem("All Languages", None)
        self.lang_filter.addItems([
            "Python", "Kotlin", "JavaScript", "TypeScript", "Java",
            "SQL", "HTML", "CSS", "JSON", "XML"
        ])
        self.lang_filter.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px;
                color: #e5e7eb;
            }
        """)
        self.lang_filter.currentIndexChanged.connect(lambda: self._load_snippets())
        filter_layout.addWidget(QLabel("Filter:"))
        filter_layout.addWidget(self.lang_filter, 1)
        left_layout.addLayout(filter_layout)
        
        # Snippet list
        self.snippet_list = QListWidget()
        self.snippet_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: #374151;
                border-radius: 6px;
                padding: 10px;
                margin: 4px 0;
                color: #e5e7eb;
            }
            QListWidget::item:selected {
                background-color: rgba(99, 102, 241, 0.3);
                border: 1px solid #6366f1;
            }
            QListWidget::item:hover {
                background-color: #4b5563;
            }
        """)
        self.snippet_list.itemClicked.connect(self._on_snippet_clicked)
        self.snippet_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.snippet_list.customContextMenuRequested.connect(self._show_context_menu)
        left_layout.addWidget(self.snippet_list)
        
        splitter.addWidget(left_panel)
        
        # Right panel - Code viewer
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)
        
        # Snippet info
        self.info_frame = QFrame()
        info_layout = QHBoxLayout(self.info_frame)
        info_layout.setContentsMargins(0, 0, 0, 8)
        
        self.snippet_title = QLabel("Select a snippet")
        self.snippet_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #f3f4f6;
            }
        """)
        info_layout.addWidget(self.snippet_title)
        
        info_layout.addStretch()
        
        self.lang_label = QLabel()
        self.lang_label.setStyleSheet("""
            QLabel {
                background-color: #374151;
                border-radius: 4px;
                padding: 4px 8px;
                color: #10b981;
                font-size: 12px;
            }
        """)
        info_layout.addWidget(self.lang_label)
        
        right_layout.addWidget(self.info_frame)
        
        # Description
        self.desc_label = QLabel()
        self.desc_label.setStyleSheet("""
            QLabel {
                color: #9ca3af;
                font-size: 13px;
            }
        """)
        self.desc_label.setWordWrap(True)
        right_layout.addWidget(self.desc_label)
        
        # Code viewer
        self.code_view = QPlainTextEdit()
        self.code_view.setReadOnly(True)
        self.code_view.setStyleSheet("""
            QPlainTextEdit {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
                color: #e5e7eb;
                font-family: 'Consolas', 'Fira Code', monospace;
                font-size: 13px;
            }
        """)
        self._code_highlighter = CodeHighlighter("python", self.code_view.document())
        right_layout.addWidget(self.code_view, 1)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        copy_btn = QPushButton("📋 Copy Code")
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
        copy_btn.clicked.connect(self._copy_code)
        actions_layout.addWidget(copy_btn)
        
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 10px 20px;
                color: #e5e7eb;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        edit_btn.clicked.connect(self._edit_snippet)
        actions_layout.addWidget(edit_btn)
        
        actions_layout.addStretch()
        
        right_layout.addLayout(actions_layout)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter, 1)
    
    def _load_snippets(self, search_query: str = ""):
        """Load snippets into the list"""
        self.snippet_list.clear()
        
        session = get_session()
        query = session.query(CodeSnippet)
        
        # Filter by language
        lang_filter = self.lang_filter.currentText()
        if lang_filter and lang_filter != "All Languages":
            query = query.filter(CodeSnippet.language == lang_filter.lower())
        
        # Search
        if search_query:
            search = f"%{search_query}%"
            query = query.filter(
                (CodeSnippet.title.ilike(search)) |
                (CodeSnippet.description.ilike(search)) |
                (CodeSnippet.code.ilike(search))
            )
        
        snippets = query.order_by(CodeSnippet.is_favorite.desc(), CodeSnippet.updated_at.desc()).all()
        
        for snippet in snippets:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, snippet.id)
            
            # Format display text
            text = f"{'⭐ ' if snippet.is_favorite else ''}{snippet.title}\n"
            text += f"📝 {snippet.language.upper()}"
            if snippet.description:
                text += f" • {snippet.description[:40]}..."
            
            item.setText(text)
            self.snippet_list.addItem(item)
        
        session.close()
    
    def _on_search(self, text: str):
        """Handle search"""
        self._load_snippets(text)
    
    def _on_snippet_clicked(self, item: QListWidgetItem):
        """Handle snippet selection"""
        snippet_id = item.data(Qt.ItemDataRole.UserRole)
        
        session = get_session()
        snippet = session.query(CodeSnippet).get(snippet_id)
        
        if snippet:
            self._current_snippet = snippet
            self.snippet_title.setText(snippet.title)
            self.lang_label.setText(snippet.language.upper())
            self.desc_label.setText(snippet.description or "No description")
            self.code_view.setPlainText(snippet.code)
            self._code_highlighter.set_language(snippet.language)
            
            # Update usage count
            snippet.usage_count += 1
            session.commit()
        
        session.close()
    
    def _new_snippet(self):
        """Create a new snippet"""
        session = get_session()
        categories = session.query(SnippetCategory).all()
        session.close()
        
        dialog = SnippetDialog(categories=categories, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_snippets()
    
    def _edit_snippet(self):
        """Edit current snippet"""
        if not self._current_snippet:
            return
        
        session = get_session()
        snippet = session.query(CodeSnippet).get(self._current_snippet.id)
        categories = session.query(SnippetCategory).all()
        session.close()
        
        dialog = SnippetDialog(snippet=snippet, categories=categories, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_snippets()
            # Reload the current snippet
            session = get_session()
            snippet = session.query(CodeSnippet).get(self._current_snippet.id)
            if snippet:
                self._current_snippet = snippet
                self.snippet_title.setText(snippet.title)
                self.desc_label.setText(snippet.description or "No description")
                self.code_view.setPlainText(snippet.code)
            session.close()
    
    def _copy_code(self):
        """Copy code to clipboard"""
        if self._current_snippet:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(self._current_snippet.code)
            
            # Show brief feedback
            original = self.snippet_title.text()
            self.snippet_title.setText("✅ Copied to clipboard!")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self.snippet_title.setText(original))
    
    def _show_context_menu(self, pos):
        """Show context menu for snippet"""
        item = self.snippet_list.itemAt(pos)
        if not item:
            return
        
        snippet_id = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                color: #e5e7eb;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #4b5563;
            }
        """)
        
        edit_action = menu.addAction("✏️ Edit")
        edit_action.triggered.connect(lambda: self._edit_snippet_by_id(snippet_id))
        
        favorite_action = menu.addAction("⭐ Toggle Favorite")
        favorite_action.triggered.connect(lambda: self._toggle_favorite(snippet_id))
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(lambda: self._delete_snippet(snippet_id))
        
        menu.exec(self.snippet_list.mapToGlobal(pos))
    
    def _edit_snippet_by_id(self, snippet_id: int):
        """Edit snippet by ID"""
        session = get_session()
        snippet = session.query(CodeSnippet).get(snippet_id)
        categories = session.query(SnippetCategory).all()
        session.close()
        
        if snippet:
            dialog = SnippetDialog(snippet=snippet, categories=categories, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._load_snippets()
    
    def _toggle_favorite(self, snippet_id: int):
        """Toggle favorite status"""
        session = get_session()
        snippet = session.query(CodeSnippet).get(snippet_id)
        if snippet:
            snippet.is_favorite = not snippet.is_favorite
            session.commit()
        session.close()
        self._load_snippets()
    
    def _delete_snippet(self, snippet_id: int):
        """Delete a snippet"""
        reply = QMessageBox.question(
            self, "Delete Snippet",
            "Are you sure you want to delete this snippet?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            session = get_session()
            snippet = session.query(CodeSnippet).get(snippet_id)
            if snippet:
                session.delete(snippet)
                session.commit()
            session.close()
            self._load_snippets()
            
            if self._current_snippet and self._current_snippet.id == snippet_id:
                self._current_snippet = None
                self.snippet_title.setText("Select a snippet")
                self.desc_label.setText("")
                self.code_view.clear()

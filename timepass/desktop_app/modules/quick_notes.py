"""
Quick Notes Module - Lightweight note-taking with search and organization
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QLineEdit, QTextEdit,
    QListWidget, QListWidgetItem, QSplitter, QComboBox,
    QMenu, QMessageBox, QScrollArea, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter
from datetime import datetime
from typing import Optional, List
import re

from core.database import QuickNote, NoteFolder, get_session


class MarkdownHighlighter(QSyntaxHighlighter):
    """Simple Markdown syntax highlighter"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []
        
        # Headers
        header_format = QTextCharFormat()
        header_format.setFontWeight(QFont.Weight.Bold)
        header_format.setForeground(QColor("#818cf8"))
        self._rules.append((re.compile(r'^#{1,6}\s.*$', re.MULTILINE), header_format))
        
        # Bold
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Weight.Bold)
        self._rules.append((re.compile(r'\*\*[^*]+\*\*'), bold_format))
        self._rules.append((re.compile(r'__[^_]+__'), bold_format))
        
        # Italic
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        self._rules.append((re.compile(r'\*[^*]+\*'), italic_format))
        self._rules.append((re.compile(r'_[^_]+_'), italic_format))
        
        # Code
        code_format = QTextCharFormat()
        code_format.setFontFamily("Consolas")
        code_format.setForeground(QColor("#10b981"))
        code_format.setBackground(QColor("#1f2937"))
        self._rules.append((re.compile(r'`[^`]+`'), code_format))
        
        # Links
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#3b82f6"))
        link_format.setFontUnderline(True)
        self._rules.append((re.compile(r'\[([^\]]+)\]\([^)]+\)'), link_format))
        
        # Lists
        list_format = QTextCharFormat()
        list_format.setForeground(QColor("#f59e0b"))
        self._rules.append((re.compile(r'^\s*[-*+]\s', re.MULTILINE), list_format))
        self._rules.append((re.compile(r'^\s*\d+\.\s', re.MULTILINE), list_format))
    
    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class NoteCard(QFrame):
    """Note card widget for grid/list view"""
    
    clicked = pyqtSignal(int)
    delete_requested = pyqtSignal(int)
    pin_toggled = pyqtSignal(int, bool)
    
    def __init__(self, note: QuickNote, parent=None):
        super().__init__(parent)
        self.note = note
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header with pin and menu
        header = QHBoxLayout()
        
        if self.note.is_pinned:
            pin_label = QLabel("📌")
            header.addWidget(pin_label)
        
        title = self.note.title or "Untitled"
        title_label = QLabel(title[:30] + ("..." if len(title) > 30 else ""))
        title_label.setStyleSheet("""
            QLabel {
                color: #f3f4f6;
                font-size: 14px;
                font-weight: 600;
            }
        """)
        header.addWidget(title_label, 1)
        
        menu_btn = QPushButton("⋮")
        menu_btn.setFixedSize(24, 24)
        menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #6b7280;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #e5e7eb;
            }
        """)
        menu_btn.clicked.connect(self._show_menu)
        header.addWidget(menu_btn)
        
        layout.addLayout(header)
        
        # Preview
        preview = self.note.content[:100] if self.note.content else ""
        preview = preview.replace('\n', ' ')
        if len(self.note.content or "") > 100:
            preview += "..."
        
        preview_label = QLabel(preview or "No content")
        preview_label.setWordWrap(True)
        preview_label.setStyleSheet("""
            QLabel {
                color: #9ca3af;
                font-size: 12px;
            }
        """)
        layout.addWidget(preview_label, 1)
        
        # Date
        date_str = self.note.updated_at.strftime("%d %b %Y, %H:%M")
        date_label = QLabel(date_str)
        date_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 10px;
            }
        """)
        layout.addWidget(date_label)
        
        # Styling
        bg_color = self.note.color or "#1f2937"
        border_color = "#374151" if not self.note.is_pinned else "#6366f1"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 10px;
                border: 1px solid {border_color};
            }}
            QFrame:hover {{
                border: 1px solid #6366f1;
            }}
        """)
        self.setFixedSize(240, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.note.id)
        super().mousePressEvent(event)
    
    def _show_menu(self):
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
        
        pin_action = menu.addAction("📌 Unpin" if self.note.is_pinned else "📌 Pin")
        pin_action.triggered.connect(lambda: self.pin_toggled.emit(self.note.id, not self.note.is_pinned))
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.note.id))
        
        menu.exec(self.mapToGlobal(self.rect().bottomRight()))


class NoteEditor(QFrame):
    """Note editor with markdown support"""
    
    note_saved = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_note: Optional[QuickNote] = None
        self._auto_save_timer = QTimer()
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Title
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Note title")
        self.title_edit.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                border-bottom: 1px solid #374151;
                padding: 8px 0;
                color: #f3f4f6;
                font-size: 18px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border-bottom: 2px solid #6366f1;
            }
        """)
        self.title_edit.textChanged.connect(self._on_content_changed)
        layout.addWidget(self.title_edit)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Color selector
        self.color_combo = QComboBox()
        colors = [
            ("#1f2937", "Default"),
            ("#1e3a5f", "Blue"),
            ("#1e3a3a", "Teal"),
            ("#3a1e3a", "Purple"),
            ("#3a3a1e", "Yellow"),
            ("#3a1e1e", "Red"),
            ("#1e3a1e", "Green")
        ]
        for color, name in colors:
            self.color_combo.addItem(name, color)
        self.color_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 4px 8px;
                color: #e5e7eb;
                min-width: 80px;
            }
        """)
        self.color_combo.currentIndexChanged.connect(self._on_content_changed)
        toolbar.addWidget(QLabel("Color:"))
        toolbar.addWidget(self.color_combo)
        
        toolbar.addStretch()
        
        # Pin button
        self.pin_btn = QPushButton("📌 Pin")
        self.pin_btn.setCheckable(True)
        self.pin_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 4px 12px;
                color: #9ca3af;
            }
            QPushButton:checked {
                background-color: rgba(99, 102, 241, 0.2);
                border-color: #6366f1;
                color: #818cf8;
            }
        """)
        self.pin_btn.clicked.connect(self._on_content_changed)
        toolbar.addWidget(self.pin_btn)
        
        layout.addLayout(toolbar)
        
        # Content editor
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Start writing... (Markdown supported)")
        self.content_edit.setStyleSheet("""
            QTextEdit {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
                color: #e5e7eb;
                font-size: 14px;
                font-family: 'Consolas', monospace;
            }
        """)
        self.content_edit.textChanged.connect(self._on_content_changed)
        
        # Add syntax highlighter
        self._highlighter = MarkdownHighlighter(self.content_edit.document())
        
        layout.addWidget(self.content_edit, 1)
        
        # Tags
        tags_layout = QHBoxLayout()
        tags_layout.addWidget(QLabel("Tags:"))
        
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("tag1, tag2, tag3")
        self.tags_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px;
                color: #e5e7eb;
            }
        """)
        self.tags_edit.textChanged.connect(self._on_content_changed)
        tags_layout.addWidget(self.tags_edit, 1)
        
        layout.addLayout(tags_layout)
        
        self.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
            }
            QLabel {
                color: #9ca3af;
                font-size: 12px;
            }
        """)
    
    def load_note(self, note: QuickNote):
        """Load a note into the editor"""
        self._auto_save_timer.stop()
        self._current_note = note
        
        self.title_edit.setText(note.title or "")
        self.content_edit.setText(note.content or "")
        self.pin_btn.setChecked(note.is_pinned)
        self.tags_edit.setText(", ".join(note.tags or []))
        
        # Set color
        index = self.color_combo.findData(note.color or "#1f2937")
        if index >= 0:
            self.color_combo.setCurrentIndex(index)
    
    def new_note(self):
        """Create a new note"""
        self._auto_save_timer.stop()
        
        session = get_session()
        note = QuickNote(
            title="",
            content="",
            is_pinned=False
        )
        session.add(note)
        session.commit()
        note_id = note.id
        session.close()
        
        # Reload and load into editor
        session = get_session()
        note = session.query(QuickNote).get(note_id)
        self._current_note = note
        session.close()
        
        self.title_edit.clear()
        self.content_edit.clear()
        self.pin_btn.setChecked(False)
        self.tags_edit.clear()
        self.color_combo.setCurrentIndex(0)
        
        self.title_edit.setFocus()
        self.note_saved.emit()
    
    def _on_content_changed(self):
        """Content changed - start auto-save timer"""
        self._auto_save_timer.stop()
        self._auto_save_timer.start(1000)  # Save after 1 second of inactivity
    
    def _auto_save(self):
        """Auto-save the current note"""
        self._auto_save_timer.stop()
        
        if not self._current_note:
            return
        
        session = get_session()
        note = session.query(QuickNote).get(self._current_note.id)
        
        if note:
            note.title = self.title_edit.text().strip() or None
            note.content = self.content_edit.toPlainText()
            note.is_pinned = self.pin_btn.isChecked()
            note.color = self.color_combo.currentData()
            note.tags = [t.strip() for t in self.tags_edit.text().split(",") if t.strip()]
            note.updated_at = datetime.utcnow()
            session.commit()
        
        session.close()
        self.note_saved.emit()


class QuickNotesModule(QWidget):
    """Quick Notes Module"""
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        self._setup_ui()
        self._load_notes()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📝 Quick Notes")
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
        self.search_edit.setPlaceholderText("🔍 Search notes...")
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
        
        # New note button
        new_btn = QPushButton("+ New Note")
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
        new_btn.clicked.connect(self._new_note)
        header_layout.addWidget(new_btn)
        
        layout.addLayout(header_layout)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Notes grid
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: transparent;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 8, 0)
        
        # Notes scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        
        self.notes_container = QWidget()
        self.notes_layout = QGridLayout(self.notes_container)
        self.notes_layout.setSpacing(12)
        self.notes_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        scroll.setWidget(self.notes_container)
        left_layout.addWidget(scroll)
        
        splitter.addWidget(left_panel)
        
        # Right panel - Editor
        self.editor = NoteEditor()
        self.editor.note_saved.connect(self._load_notes)
        splitter.addWidget(self.editor)
        
        splitter.setSizes([500, 500])
        
        layout.addWidget(splitter, 1)
    
    def _load_notes(self, search_query: str = ""):
        """Load notes into the grid"""
        # Clear existing cards
        while self.notes_layout.count():
            item = self.notes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        session = get_session()
        
        query = session.query(QuickNote)
        
        if search_query:
            search = f"%{search_query}%"
            query = query.filter(
                (QuickNote.title.ilike(search)) |
                (QuickNote.content.ilike(search))
            )
        
        # Get pinned first, then by date
        notes = query.order_by(
            QuickNote.is_pinned.desc(),
            QuickNote.updated_at.desc()
        ).all()
        
        row, col = 0, 0
        max_cols = 3
        
        for note in notes:
            card = NoteCard(note)
            card.clicked.connect(self._on_note_clicked)
            card.delete_requested.connect(self._delete_note)
            card.pin_toggled.connect(self._toggle_pin)
            
            self.notes_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        session.close()
    
    def _on_search(self, text: str):
        """Handle search input"""
        self._load_notes(text)
    
    def _new_note(self):
        """Create a new note"""
        self.editor.new_note()
    
    def _on_note_clicked(self, note_id: int):
        """Handle note click"""
        session = get_session()
        note = session.query(QuickNote).get(note_id)
        if note:
            self.editor.load_note(note)
        session.close()
    
    def _delete_note(self, note_id: int):
        """Delete a note"""
        reply = QMessageBox.question(
            self, "Delete Note",
            "Are you sure you want to delete this note?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            session = get_session()
            note = session.query(QuickNote).get(note_id)
            if note:
                session.delete(note)
                session.commit()
            session.close()
            self._load_notes()
    
    def _toggle_pin(self, note_id: int, pinned: bool):
        """Toggle note pin status"""
        session = get_session()
        note = session.query(QuickNote).get(note_id)
        if note:
            note.is_pinned = pinned
            session.commit()
        session.close()
        self._load_notes()

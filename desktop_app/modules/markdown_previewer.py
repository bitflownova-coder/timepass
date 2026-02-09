"""
Markdown Previewer Module - Live markdown preview with export
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QPushButton, QPlainTextEdit,
    QSplitter, QFileDialog, QComboBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter
from PyQt6.QtWebEngineWidgets import QWebEngineView
import re

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


class MarkdownHighlighter(QSyntaxHighlighter):
    """Markdown syntax highlighter"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []
        
        # Headers
        header_format = QTextCharFormat()
        header_format.setForeground(QColor("#82aaff"))
        header_format.setFontWeight(700)
        self._rules.append((re.compile(r'^#{1,6}\s.*$', re.MULTILINE), header_format))
        
        # Bold
        bold_format = QTextCharFormat()
        bold_format.setForeground(QColor("#f78c6c"))
        bold_format.setFontWeight(700)
        self._rules.append((re.compile(r'\*\*[^*]+\*\*'), bold_format))
        self._rules.append((re.compile(r'__[^_]+__'), bold_format))
        
        # Italic
        italic_format = QTextCharFormat()
        italic_format.setForeground(QColor("#c3e88d"))
        italic_format.setFontItalic(True)
        self._rules.append((re.compile(r'\*[^*]+\*'), italic_format))
        self._rules.append((re.compile(r'_[^_]+_'), italic_format))
        
        # Code inline
        code_format = QTextCharFormat()
        code_format.setForeground(QColor("#ffcb6b"))
        code_format.setFontFamily("Consolas")
        self._rules.append((re.compile(r'`[^`]+`'), code_format))
        
        # Code block
        block_format = QTextCharFormat()
        block_format.setForeground(QColor("#c792ea"))
        self._rules.append((re.compile(r'^```.*$', re.MULTILINE), block_format))
        
        # Links
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#89ddff"))
        self._rules.append((re.compile(r'\[([^\]]+)\]\([^)]+\)'), link_format))
        
        # Lists
        list_format = QTextCharFormat()
        list_format.setForeground(QColor("#f78c6c"))
        self._rules.append((re.compile(r'^[\s]*[-*+]\s', re.MULTILINE), list_format))
        self._rules.append((re.compile(r'^[\s]*\d+\.\s', re.MULTILINE), list_format))
        
        # Blockquote
        quote_format = QTextCharFormat()
        quote_format.setForeground(QColor("#676e95"))
        self._rules.append((re.compile(r'^>\s.*$', re.MULTILINE), quote_format))
    
    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class MarkdownPreviewerModule(QWidget):
    """Markdown Previewer Module"""
    
    CSS_THEMES = {
        "Dark": """
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background-color: #111827;
                color: #e5e7eb;
                padding: 20px;
                line-height: 1.6;
            }
            h1, h2, h3, h4, h5, h6 { color: #f9fafb; margin-top: 1.5em; }
            h1 { font-size: 2em; border-bottom: 1px solid #374151; padding-bottom: 0.3em; }
            h2 { font-size: 1.5em; border-bottom: 1px solid #374151; padding-bottom: 0.3em; }
            a { color: #60a5fa; text-decoration: none; }
            a:hover { text-decoration: underline; }
            code {
                background-color: #1f2937;
                padding: 0.2em 0.4em;
                border-radius: 4px;
                font-family: 'Consolas', monospace;
                color: #fbbf24;
            }
            pre {
                background-color: #1f2937;
                padding: 16px;
                border-radius: 8px;
                overflow-x: auto;
            }
            pre code { background: none; padding: 0; color: #e5e7eb; }
            blockquote {
                border-left: 4px solid #6366f1;
                margin: 1em 0;
                padding-left: 1em;
                color: #9ca3af;
            }
            table { border-collapse: collapse; width: 100%; }
            th, td {
                border: 1px solid #374151;
                padding: 8px 12px;
                text-align: left;
            }
            th { background-color: #1f2937; }
            img { max-width: 100%; height: auto; border-radius: 8px; }
            hr { border: none; border-top: 1px solid #374151; margin: 2em 0; }
            ul, ol { padding-left: 2em; }
            li { margin: 0.5em 0; }
        """,
        "Light": """
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background-color: #ffffff;
                color: #1f2937;
                padding: 20px;
                line-height: 1.6;
            }
            h1, h2, h3, h4, h5, h6 { color: #111827; margin-top: 1.5em; }
            h1 { font-size: 2em; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.3em; }
            h2 { font-size: 1.5em; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.3em; }
            a { color: #2563eb; text-decoration: none; }
            a:hover { text-decoration: underline; }
            code {
                background-color: #f3f4f6;
                padding: 0.2em 0.4em;
                border-radius: 4px;
                font-family: 'Consolas', monospace;
                color: #b45309;
            }
            pre {
                background-color: #f3f4f6;
                padding: 16px;
                border-radius: 8px;
                overflow-x: auto;
            }
            pre code { background: none; padding: 0; color: #1f2937; }
            blockquote {
                border-left: 4px solid #6366f1;
                margin: 1em 0;
                padding-left: 1em;
                color: #6b7280;
            }
            table { border-collapse: collapse; width: 100%; }
            th, td {
                border: 1px solid #e5e7eb;
                padding: 8px 12px;
                text-align: left;
            }
            th { background-color: #f9fafb; }
            img { max-width: 100%; height: auto; border-radius: 8px; }
            hr { border: none; border-top: 1px solid #e5e7eb; margin: 2em 0; }
            ul, ol { padding-left: 2em; }
            li { margin: 0.5em 0; }
        """,
        "GitHub": """
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
                background-color: #0d1117;
                color: #c9d1d9;
                padding: 20px;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
            }
            h1, h2, h3, h4, h5, h6 { color: #c9d1d9; margin-top: 24px; margin-bottom: 16px; font-weight: 600; }
            h1 { font-size: 2em; border-bottom: 1px solid #21262d; padding-bottom: 0.3em; }
            h2 { font-size: 1.5em; border-bottom: 1px solid #21262d; padding-bottom: 0.3em; }
            a { color: #58a6ff; text-decoration: none; }
            a:hover { text-decoration: underline; }
            code {
                background-color: rgba(110,118,129,0.4);
                padding: 0.2em 0.4em;
                border-radius: 6px;
                font-family: 'SFMono-Regular', Consolas, monospace;
                font-size: 85%;
            }
            pre {
                background-color: #161b22;
                padding: 16px;
                border-radius: 6px;
                overflow-x: auto;
            }
            pre code { background: none; padding: 0; font-size: 100%; }
            blockquote {
                border-left: 4px solid #3b5998;
                margin: 0;
                padding: 0 1em;
                color: #8b949e;
            }
            table { border-collapse: collapse; width: 100%; }
            th, td {
                border: 1px solid #30363d;
                padding: 6px 13px;
            }
            th { background-color: #161b22; }
            tr:nth-child(even) { background-color: #161b22; }
            img { max-width: 100%; }
            hr { border: none; border-top: 1px solid #21262d; margin: 24px 0; }
        """
    }
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        self._current_theme = "Dark"
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._update_preview)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📝 Markdown Previewer")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f9fafb;
            }
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Theme selector
        header_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(self.CSS_THEMES.keys()))
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 6px 12px;
                color: #e5e7eb;
            }
        """)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        header_layout.addWidget(self.theme_combo)
        
        # Action buttons
        open_btn = QPushButton("📂 Open")
        open_btn.setStyleSheet(self._button_style())
        open_btn.clicked.connect(self._open_file)
        header_layout.addWidget(open_btn)
        
        save_btn = QPushButton("💾 Save")
        save_btn.setStyleSheet(self._button_style())
        save_btn.clicked.connect(self._save_file)
        header_layout.addWidget(save_btn)
        
        export_btn = QPushButton("📤 Export HTML")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        export_btn.clicked.connect(self._export_html)
        header_layout.addWidget(export_btn)
        
        layout.addLayout(header_layout)
        
        if not HAS_MARKDOWN:
            warning = QLabel("⚠️ markdown library not installed. Run: pip install markdown")
            warning.setStyleSheet("color: #f59e0b; padding: 10px;")
            layout.addWidget(warning)
        
        # Splitter for editor and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Editor panel
        self.editor_frame = QFrame(self)
        self.editor_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        editor_layout = QVBoxLayout(self.editor_frame)
        editor_layout.setContentsMargins(12, 12, 12, 12)
        
        editor_header = QHBoxLayout()
        editor_label = QLabel("Editor")
        editor_label.setStyleSheet("color: #9ca3af; font-weight: bold;")
        editor_header.addWidget(editor_label)
        editor_header.addStretch()
        
        # Word count
        self.word_count_label = QLabel("0 words, 0 chars")
        self.word_count_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        editor_header.addWidget(self.word_count_label)
        
        editor_layout.addLayout(editor_header)
        
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Write your markdown here...")
        self.editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #111827;
                border: none;
                border-radius: 8px;
                padding: 12px;
                color: #e5e7eb;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        self._highlighter = MarkdownHighlighter(self.editor.document())
        self.editor.textChanged.connect(self._on_text_changed)
        editor_layout.addWidget(self.editor)
        
        splitter.addWidget(self.editor_frame)
        
        # Preview panel
        self.preview_frame = QFrame(self)
        self.preview_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(12, 12, 12, 12)
        
        preview_header = QHBoxLayout()
        preview_label = QLabel("Preview")
        preview_label.setStyleSheet("color: #9ca3af; font-weight: bold;")
        preview_header.addWidget(preview_label)
        preview_header.addStretch()
        
        copy_html_btn = QPushButton("📋 Copy HTML")
        copy_html_btn.setStyleSheet("""
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
        copy_html_btn.clicked.connect(self._copy_html)
        preview_header.addWidget(copy_html_btn)
        
        preview_layout.addLayout(preview_header)
        
        self.preview = QWebEngineView()
        self.preview.setStyleSheet("border-radius: 8px;")
        preview_layout.addWidget(self.preview)
        
        splitter.addWidget(self.preview_frame)
        splitter.setSizes([500, 500])
        
        layout.addWidget(splitter, 1)
        
        # Quick format toolbar
        self.format_frame = QFrame(self)
        self.format_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 8px;
                border: 1px solid #374151;
            }
        """)
        format_layout = QHBoxLayout(self.format_frame)
        format_layout.setContentsMargins(12, 8, 12, 8)
        format_layout.setSpacing(4)
        
        format_buttons = [
            ("B", "**bold**", "Bold"),
            ("I", "*italic*", "Italic"),
            ("S", "~~strike~~", "Strikethrough"),
            ("H1", "# ", "Heading 1"),
            ("H2", "## ", "Heading 2"),
            ("🔗", "[text](url)", "Link"),
            ("📷", "![alt](url)", "Image"),
            ("📋", "```\ncode\n```", "Code Block"),
            ("`", "`code`", "Inline Code"),
            ("•", "- ", "Bullet List"),
            ("1.", "1. ", "Numbered List"),
            (">", "> ", "Quote"),
            ("—", "---", "Horizontal Rule"),
            ("📊", "| Col | Col |\n|-----|-----|\n| Cell | Cell |", "Table"),
        ]
        
        for label, insert, tooltip in format_buttons:
            btn = QPushButton(label)
            btn.setFixedSize(32, 32)
            btn.setToolTip(tooltip)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #374151;
                    border: none;
                    border-radius: 4px;
                    color: #e5e7eb;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #4b5563;
                }
            """)
            btn.clicked.connect(lambda checked, t=insert: self._insert_format(t))
            format_layout.addWidget(btn)
        
        format_layout.addStretch()
        layout.addWidget(self.format_frame)
        
        # Initial preview
        self._set_sample_markdown()
    
    def _button_style(self) -> str:
        return """
            QPushButton {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 8px 16px;
                color: #e5e7eb;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """
    
    def _on_text_changed(self):
        """Handle text change with debounce"""
        self._update_timer.stop()
        self._update_timer.start(300)
        
        # Update word count
        text = self.editor.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.word_count_label.setText(f"{words} words, {chars} chars")
    
    def _update_preview(self):
        """Update markdown preview"""
        text = self.editor.toPlainText()
        
        if HAS_MARKDOWN:
            html_content = markdown.markdown(
                text,
                extensions=['tables', 'fenced_code', 'codehilite', 'toc']
            )
        else:
            # Basic conversion without library
            html_content = text.replace('\n', '<br>')
        
        css = self.CSS_THEMES.get(self._current_theme, self.CSS_THEMES["Dark"])
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>{css}</style>
        </head>
        <body>{html_content}</body>
        </html>
        """
        
        self.preview.setHtml(full_html)
    
    def _on_theme_changed(self, theme: str):
        """Handle theme change"""
        self._current_theme = theme
        self._update_preview()
    
    def _insert_format(self, text: str):
        """Insert format text at cursor"""
        cursor = self.editor.textCursor()
        cursor.insertText(text)
        self.editor.setFocus()
    
    def _open_file(self):
        """Open markdown file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Markdown File",
            "",
            "Markdown Files (*.md *.markdown);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.editor.setPlainText(f.read())
            except Exception as e:
                pass  # Handle error
    
    def _save_file(self):
        """Save markdown file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Markdown File",
            "document.md",
            "Markdown Files (*.md);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.editor.toPlainText())
            except Exception as e:
                pass  # Handle error
    
    def _export_html(self):
        """Export as HTML"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export HTML",
            "document.html",
            "HTML Files (*.html);;All Files (*)"
        )
        
        if file_path:
            text = self.editor.toPlainText()
            
            if HAS_MARKDOWN:
                html_content = markdown.markdown(
                    text,
                    extensions=['tables', 'fenced_code', 'codehilite', 'toc']
                )
            else:
                html_content = text.replace('\n', '<br>')
            
            css = self.CSS_THEMES.get(self._current_theme, self.CSS_THEMES["Dark"])
            
            full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Markdown Export</title>
    <style>{css}</style>
</head>
<body>
{html_content}
</body>
</html>"""
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(full_html)
            except Exception as e:
                pass  # Handle error
    
    def _copy_html(self):
        """Copy rendered HTML to clipboard"""
        text = self.editor.toPlainText()
        
        if HAS_MARKDOWN:
            html_content = markdown.markdown(text, extensions=['tables', 'fenced_code'])
        else:
            html_content = text.replace('\n', '<br>')
        
        clipboard = QApplication.clipboard()
        clipboard.setText(html_content)
    
    def _set_sample_markdown(self):
        """Set sample markdown content"""
        sample = """# Welcome to Markdown Previewer

This is a **live preview** of your markdown content.

## Features

- Real-time preview
- Syntax highlighting
- Multiple themes
- Export to HTML

### Code Example

```python
def hello_world():
    print("Hello, World!")
```

### Table Example

| Feature | Status |
|---------|--------|
| Preview | ✅ |
| Export | ✅ |
| Themes | ✅ |

> This is a blockquote. It's useful for highlighting important information.

---

Try editing this content to see the live preview!
"""
        self.editor.setPlainText(sample)
        self._update_preview()

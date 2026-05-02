"""
Web Crawler Module - Wrapper around website_crawler
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QPushButton, QLineEdit, QTextEdit,
    QListWidget, QListWidgetItem, QProgressBar, QSpinBox,
    QMessageBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
import json
import os
import sys
import uuid
from datetime import datetime

# Add parent directory to path for imports
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CRAWLER_PATH = os.path.join(WORKSPACE_ROOT, "website_crawler")


class CrawlWorker(QThread):
    """Background worker for crawling"""
    
    progress_update = pyqtSignal(str)
    crawl_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, url: str, max_pages: int = 50, max_depth: int = 2):
        super().__init__()
        self.url = url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self._stop = False
    
    def run(self):
        """Run the crawl"""
        try:
            # Try to import crawler
            sys.path.insert(0, CRAWLER_PATH)
            from crawler import WebCrawler
            
            crawl_id = str(uuid.uuid4())
            output_dir = os.path.join(CRAWLER_PATH, "output", crawl_id)
            os.makedirs(output_dir, exist_ok=True)
            
            crawler = WebCrawler(
                base_url=self.url,
                max_pages=self.max_pages,
                max_depth=self.max_depth,
                output_dir=output_dir
            )
            
            self.progress_update.emit(f"Starting crawl of {self.url}...")
            
            # Run crawl
            result = crawler.crawl()
            
            self.crawl_complete.emit({
                "id": crawl_id,
                "url": self.url,
                "pages": len(result.get("pages", [])),
                "output_dir": output_dir,
                "data": result
            })
            
        except ImportError as e:
            self.error_occurred.emit(f"Crawler module not available: {e}")
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def stop(self):
        self._stop = True


class WebCrawlerModule(QWidget):
    """Web Crawler Module"""
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        self._worker = None
        self._setup_ui()
        self._load_history()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        title = QLabel("🕷️ Web Crawler")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
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
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: #1f2937;
                color: #f9fafb;
            }
        """)
        
        # New Crawl tab
        crawl_tab = self._create_crawl_tab()
        tabs.addTab(crawl_tab, "🚀 New Crawl")
        
        # History tab
        history_tab = self._create_history_tab()
        tabs.addTab(history_tab, "📜 History")
        
        layout.addWidget(tabs, 1)
    
    def _create_crawl_tab(self):
        """Create new crawl tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # URL input
        self.url_frame = QFrame(self)
        self.url_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
            }
        """)
        url_layout = QVBoxLayout(self.url_frame)
        url_layout.setContentsMargins(16, 16, 16, 16)
        
        url_layout.addWidget(QLabel("Target URL"))
        
        url_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        self.url_input.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 12px;
                color: #e5e7eb;
                font-size: 14px;
            }
        """)
        url_row.addWidget(self.url_input)
        
        url_layout.addLayout(url_row)
        layout.addWidget(self.url_frame)
        
        # Options
        self.crawl_options_frame = QFrame(self)
        self.crawl_options_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
            }
        """)
        options_layout = QHBoxLayout(self.crawl_options_frame)
        options_layout.setContentsMargins(16, 16, 16, 16)
        options_layout.setSpacing(24)
        
        # Max pages
        pages_group = QVBoxLayout()
        pages_group.addWidget(QLabel("Max Pages"))
        self.max_pages = QSpinBox()
        self.max_pages.setRange(1, 1000)
        self.max_pages.setValue(50)
        self.max_pages.setStyleSheet("""
            QSpinBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
            }
        """)
        pages_group.addWidget(self.max_pages)
        options_layout.addLayout(pages_group)
        
        # Max depth
        depth_group = QVBoxLayout()
        depth_group.addWidget(QLabel("Max Depth"))
        self.max_depth = QSpinBox()
        self.max_depth.setRange(1, 10)
        self.max_depth.setValue(2)
        self.max_depth.setStyleSheet("""
            QSpinBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
            }
        """)
        depth_group.addWidget(self.max_depth)
        options_layout.addLayout(depth_group)
        
        # Checkboxes
        options_layout.addWidget(QLabel("Options:"))
        self.extract_images = QCheckBox("Extract Images")
        self.extract_images.setChecked(True)
        self.extract_images.setStyleSheet("color: #e5e7eb;")
        options_layout.addWidget(self.extract_images)
        
        self.extract_links = QCheckBox("Extract Links")
        self.extract_links.setChecked(True)
        self.extract_links.setStyleSheet("color: #e5e7eb;")
        options_layout.addWidget(self.extract_links)
        
        options_layout.addStretch()
        layout.addWidget(self.crawl_options_frame)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🕷️ Start Crawl")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 8px;
                padding: 14px 32px;
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
        self.start_btn.clicked.connect(self._start_crawl)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                border: none;
                border-radius: 8px;
                padding: 14px 32px;
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
        self.stop_btn.clicked.connect(self._stop_crawl)
        btn_layout.addWidget(self.stop_btn)
        
        btn_layout.addStretch()
        
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #374151;
                border-radius: 4px;
                text-align: center;
                color: #e5e7eb;
            }
            QProgressBar::chunk {
                background-color: #10b981;
            }
        """)
        self.progress.setRange(0, 0)  # Indeterminate
        self.progress.hide()
        btn_layout.addWidget(self.progress, 1)
        
        layout.addLayout(btn_layout)
        
        # Log output
        layout.addWidget(QLabel("Output Log"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
                color: #10b981;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.log_output, 1)
        
        return widget
    
    def _create_history_tab(self):
        """Create history tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("Previous Crawls"))
        header.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
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
        refresh_btn.clicked.connect(self._load_history)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Crawl ID", "URL", "Pages", "Date", "Actions"])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.history_table.setStyleSheet("""
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
            QHeaderView::section {
                background-color: #1f2937;
                color: #9ca3af;
                border: none;
                padding: 10px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.history_table)
        
        return widget
    
    def _start_crawl(self):
        """Start a new crawl"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a URL")
            return
        
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.url_input.setText(url)
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress.show()
        self.log_output.clear()
        
        self._log(f"Starting crawl: {url}")
        self._log(f"Max pages: {self.max_pages.value()}")
        self._log(f"Max depth: {self.max_depth.value()}")
        
        # Start worker
        self._worker = CrawlWorker(url, self.max_pages.value(), self.max_depth.value())
        self._worker.progress_update.connect(self._log)
        self._worker.crawl_complete.connect(self._on_crawl_complete)
        self._worker.error_occurred.connect(self._on_crawl_error)
        self._worker.start()
    
    def _stop_crawl(self):
        """Stop current crawl"""
        if self._worker:
            self._worker.stop()
            self._log("Stopping crawl...")
    
    def _log(self, message: str):
        """Add log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")
    
    def _on_crawl_complete(self, result: dict):
        """Handle crawl completion"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.hide()
        
        self._log(f"✓ Crawl complete!")
        self._log(f"  Pages crawled: {result['pages']}")
        self._log(f"  Output dir: {result['output_dir']}")
        
        self._load_history()
    
    def _on_crawl_error(self, error: str):
        """Handle crawl error"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.hide()
        
        self._log(f"✗ Error: {error}")
    
    def _load_history(self):
        """Load crawl history"""
        self.history_table.setRowCount(0)
        
        crawls_file = os.path.join(CRAWLER_PATH, "output", "crawls.json")
        if os.path.exists(crawls_file):
            try:
                with open(crawls_file, "r", encoding="utf-8") as f:
                    crawls = json.load(f)
                
                for crawl in crawls:
                    row = self.history_table.rowCount()
                    self.history_table.insertRow(row)
                    
                    self.history_table.setItem(row, 0, QTableWidgetItem(crawl.get("id", "")[:8]))
                    self.history_table.setItem(row, 1, QTableWidgetItem(crawl.get("url", "")))
                    self.history_table.setItem(row, 2, QTableWidgetItem(str(crawl.get("pages_crawled", 0))))
                    self.history_table.setItem(row, 3, QTableWidgetItem(crawl.get("date", "")))
                    
                    # View button
                    view_btn = QPushButton("📂 View")
                    view_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #374151;
                            border: none;
                            border-radius: 4px;
                            padding: 4px 12px;
                            color: #e5e7eb;
                        }
                        QPushButton:hover {
                            background-color: #4b5563;
                        }
                    """)
                    crawl_id = crawl.get("id", "")
                    view_btn.clicked.connect(lambda _, cid=crawl_id: self._open_crawl_folder(cid))
                    self.history_table.setCellWidget(row, 4, view_btn)
                    
            except Exception as e:
                self._log(f"Failed to load history: {e}")
    
    def _open_crawl_folder(self, crawl_id: str):
        """Open crawl output folder"""
        import subprocess
        folder = os.path.join(CRAWLER_PATH, "output", crawl_id)
        if os.path.exists(folder):
            if sys.platform == "win32":
                subprocess.run(["explorer", folder])
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])

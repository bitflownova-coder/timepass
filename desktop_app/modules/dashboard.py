"""
Dashboard Module - Overview of all tools and quick stats
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
from typing import Dict, Any


class StatCard(QFrame):
    """Quick stat card widget"""
    
    def __init__(self, title: str, value: str, subtitle: str = "", color: str = "#6366f1", parent=None):
        super().__init__(parent)
        self._setup_ui(title, value, subtitle, color)
    
    def _setup_ui(self, title: str, value: str, subtitle: str, color: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: #9ca3af;
                font-size: 12px;
                font-weight: 500;
            }}
        """)
        layout.addWidget(title_label)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 28px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(self.value_label)
        
        # Subtitle
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("""
                QLabel {
                    color: #6b7280;
                    font-size: 11px;
                }
            """)
            layout.addWidget(sub_label)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }}
            QFrame:hover {{
                border: 1px solid {color};
            }}
        """)
    
    def update_value(self, value: str):
        self.value_label.setText(value)


class ToolCard(QFrame):
    """Quick access tool card"""
    
    clicked = pyqtSignal(str)
    
    def __init__(self, module_id: str, title: str, description: str, 
                 icon: str, color: str = "#6366f1", parent=None):
        super().__init__(parent)
        self.module_id = module_id
        self._setup_ui(title, description, icon, color)
    
    def _setup_ui(self, title: str, description: str, icon: str, color: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 32px;
                padding: 8px;
            }}
        """)
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: #f3f4f6;
                font-size: 14px;
                font-weight: 600;
            }}
        """)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                color: #9ca3af;
                font-size: 12px;
            }
        """)
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
                min-height: 140px;
            }}
            QFrame:hover {{
                border: 1px solid {color};
                background-color: #263445;
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(180, 160)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.module_id)
        super().mousePressEvent(event)


class RecentActivityItem(QFrame):
    """Recent activity item widget"""
    
    def __init__(self, activity_type: str, title: str, time: str, icon: str, parent=None):
        super().__init__(parent)
        self._setup_ui(activity_type, title, time, icon)
    
    def _setup_ui(self, activity_type: str, title: str, time: str, icon: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px;")
        icon_label.setFixedWidth(30)
        layout.addWidget(icon_label)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #e5e7eb;
                font-size: 13px;
            }
        """)
        content_layout.addWidget(title_label)
        
        meta_label = QLabel(f"{activity_type} • {time}")
        meta_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 11px;
            }
        """)
        content_layout.addWidget(meta_label)
        
        layout.addLayout(content_layout, 1)
        
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-radius: 8px;
            }
            QFrame:hover {
                background-color: rgba(255, 255, 255, 0.03);
            }
        """)


class DashboardModule(QWidget):
    """Main Dashboard Module"""
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        self._setup_ui()
        self._load_stats()
    
    def _setup_ui(self):
        """Setup dashboard UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Header
        header = QLabel("Developer Dashboard")
        header.setStyleSheet("""
            QLabel {
                color: #f9fafb;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        layout.addWidget(header)
        
        # Welcome message
        welcome = QLabel(f"Good {self._get_greeting()}, Developer! Here's your productivity overview.")
        welcome.setStyleSheet("""
            QLabel {
                color: #9ca3af;
                font-size: 14px;
            }
        """)
        layout.addWidget(welcome)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 16, 0)
        content_layout.setSpacing(24)
        
        # Stats section
        stats_label = QLabel("📊 Quick Stats")
        stats_label.setStyleSheet("""
            QLabel {
                color: #e5e7eb;
                font-size: 16px;
                font-weight: 600;
            }
        """)
        content_layout.addWidget(stats_label)
        
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        self.time_stat = StatCard("Hours This Week", "0h", "Time tracked", "#10b981")
        stats_layout.addWidget(self.time_stat)
        
        self.notes_stat = StatCard("Quick Notes", "0", "Active notes", "#6366f1")
        stats_layout.addWidget(self.notes_stat)
        
        self.snippets_stat = StatCard("Code Snippets", "0", "Saved snippets", "#f59e0b")
        stats_layout.addWidget(self.snippets_stat)
        
        self.api_stat = StatCard("API Requests", "0", "Saved requests", "#ec4899")
        stats_layout.addWidget(self.api_stat)
        
        stats_layout.addStretch()
        content_layout.addLayout(stats_layout)
        
        # Quick Tools section
        tools_label = QLabel("🛠️ Quick Tools")
        tools_label.setStyleSheet("""
            QLabel {
                color: #e5e7eb;
                font-size: 16px;
                font-weight: 600;
            }
        """)
        content_layout.addWidget(tools_label)
        
        tools_grid = QGridLayout()
        tools_grid.setSpacing(12)
        
        tools = [
            ("time_tracker", "Time Tracker", "Track time on projects", "⏱️", "#10b981"),
            ("quick_notes", "Quick Notes", "Capture ideas fast", "📝", "#6366f1"),
            ("snippets", "Snippets", "Reusable code blocks", "💻", "#f59e0b"),
            ("api_tester", "API Tester", "Test HTTP endpoints", "🔌", "#ec4899"),
            ("json_formatter", "JSON/XML", "Format & validate data", "📋", "#8b5cf6"),
            ("regex_tester", "Regex Tester", "Build & test patterns", "🔍", "#14b8a6"),
            ("encoder", "Encoder", "Base64, URL, JWT", "🔐", "#f97316"),
            ("color_converter", "Colors", "Convert color formats", "🎨", "#06b6d4"),
            ("password_gen", "Passwords", "Generate secure keys", "🔑", "#ef4444"),
            ("qr_gen", "QR Codes", "Generate QR codes", "📱", "#84cc16"),
            ("log_viewer", "Log Viewer", "Analyze log files", "📄", "#a855f7"),
            ("crawler", "Web Crawler", "Crawl websites", "🕷️", "#3b82f6"),
        ]
        
        row, col = 0, 0
        for module_id, title, desc, icon, color in tools:
            card = ToolCard(module_id, title, desc, icon, color)
            card.clicked.connect(self._on_tool_clicked)
            tools_grid.addWidget(card, row, col)
            col += 1
            if col >= 6:
                col = 0
                row += 1
        
        content_layout.addLayout(tools_grid)
        
        # Recent Activity section
        activity_label = QLabel("🕐 Recent Activity")
        activity_label.setStyleSheet("""
            QLabel {
                color: #e5e7eb;
                font-size: 16px;
                font-weight: 600;
            }
        """)
        content_layout.addWidget(activity_label)
        
        self.activity_frame = QFrame()
        self.activity_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        self.activity_layout = QVBoxLayout(self.activity_frame)
        self.activity_layout.setContentsMargins(8, 8, 8, 8)
        self.activity_layout.setSpacing(4)
        
        # Placeholder for recent activity
        no_activity = QLabel("No recent activity yet. Start using the tools!")
        no_activity.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 13px;
                padding: 20px;
            }
        """)
        no_activity.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.activity_layout.addWidget(no_activity)
        
        content_layout.addWidget(self.activity_frame)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
    
    def _get_greeting(self) -> str:
        """Get time-based greeting"""
        hour = datetime.now().hour
        if hour < 12:
            return "morning"
        elif hour < 17:
            return "afternoon"
        else:
            return "evening"
    
    def _load_stats(self):
        """Load statistics from database"""
        try:
            from core.database import TimeEntry, QuickNote, CodeSnippet, ApiRequest
            session = self.db.get_session()
            
            # Time this week
            week_start = datetime.now() - timedelta(days=datetime.now().weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            
            total_minutes = session.query(TimeEntry).filter(
                TimeEntry.start_time >= week_start
            ).with_entities(
                TimeEntry.duration_minutes
            ).all()
            
            hours = sum(t[0] or 0 for t in total_minutes) / 60
            self.time_stat.update_value(f"{hours:.1f}h")
            
            # Notes count
            notes_count = session.query(QuickNote).count()
            self.notes_stat.update_value(str(notes_count))
            
            # Snippets count
            snippets_count = session.query(CodeSnippet).count()
            self.snippets_stat.update_value(str(snippets_count))
            
            # API requests count
            api_count = session.query(ApiRequest).count()
            self.api_stat.update_value(str(api_count))
            
            session.close()
        except Exception as e:
            print(f"Error loading stats: {e}")
    
    def _on_tool_clicked(self, module_id: str):
        """Handle tool card click - navigate to module"""
        # Find main window and navigate
        parent = self.parent()
        while parent:
            if hasattr(parent, 'sidebar'):
                parent.sidebar.select_module(module_id)
                break
            parent = parent.parent()

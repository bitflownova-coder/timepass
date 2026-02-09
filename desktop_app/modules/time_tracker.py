"""
Time Tracker Module - Track time on projects and tasks
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QLineEdit, QTextEdit,
    QComboBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QMessageBox,
    QDateTimeEdit, QCheckBox, QScrollArea, QSplitter,
    QTabWidget, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QDateTime, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QAction
from datetime import datetime, timedelta
from typing import Optional, List

from core.database import Project, TimeEntry, Client, get_session


class TimerDisplay(QFrame):
    """Large timer display widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._elapsed_seconds = 0
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.time_label = QLabel("00:00:00")
        self.time_label.setStyleSheet("""
            QLabel {
                font-size: 64px;
                font-weight: bold;
                color: #10b981;
                font-family: 'Consolas', monospace;
            }
        """)
        layout.addWidget(self.time_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = QLabel("Ready to track")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
                padding: 20px;
            }
        """)
    
    def update_time(self, seconds: int):
        """Update displayed time"""
        self._elapsed_seconds = seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{secs:02d}")
    
    def set_status(self, status: str, color: str = "#6b7280"):
        """Set status text"""
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 14px;
            }}
        """)
    
    def set_running(self, running: bool):
        """Change appearance based on running state"""
        if running:
            self.time_label.setStyleSheet("""
                QLabel {
                    font-size: 64px;
                    font-weight: bold;
                    color: #10b981;
                    font-family: 'Consolas', monospace;
                }
            """)
            self.setStyleSheet("""
                QFrame {
                    background-color: #1f2937;
                    border-radius: 12px;
                    border: 2px solid #10b981;
                    padding: 20px;
                }
            """)
        else:
            self.time_label.setStyleSheet("""
                QLabel {
                    font-size: 64px;
                    font-weight: bold;
                    color: #9ca3af;
                    font-family: 'Consolas', monospace;
                }
            """)
            self.setStyleSheet("""
                QFrame {
                    background-color: #1f2937;
                    border-radius: 12px;
                    border: 1px solid #374151;
                    padding: 20px;
                }
            """)


class ProjectSelector(QComboBox):
    """Project selection combo box with add option"""
    
    project_selected = pyqtSignal(object)  # Emits Project or None
    add_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._projects: List[Project] = []
        self.setMinimumWidth(250)
        self.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 8px 12px;
                color: #e5e7eb;
                font-size: 13px;
            }
            QComboBox:hover {
                border-color: #6366f1;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #374151;
                border: 1px solid #4b5563;
                selection-background-color: #6366f1;
            }
        """)
        self.currentIndexChanged.connect(self._on_index_changed)
    
    def load_projects(self):
        """Load projects from database"""
        self.blockSignals(True)
        self.clear()
        self.addItem("No Project", None)
        self.addItem("➕ Add New Project...", "ADD_NEW")
        
        session = get_session()
        self._projects = session.query(Project).filter(Project.is_active == True).all()
        session.close()
        
        for project in self._projects:
            self.addItem(f"● {project.name}", project.id)
        
        self.blockSignals(False)
    
    def _on_index_changed(self, index: int):
        data = self.currentData()
        if data == "ADD_NEW":
            self.setCurrentIndex(0)
            self.add_requested.emit()
        else:
            project = None
            if data:
                for p in self._projects:
                    if p.id == data:
                        project = p
                        break
            self.project_selected.emit(project)


class ProjectDialog(QDialog):
    """Dialog to add/edit a project"""
    
    def __init__(self, project: Optional[Project] = None, parent=None):
        super().__init__(parent)
        self.project = project
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Add Project" if not self.project else "Edit Project")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: #1f2937;
            }
            QLabel {
                color: #e5e7eb;
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
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
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Project name")
        form.addRow("Name:", self.name_edit)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText("Description (optional)")
        form.addRow("Description:", self.desc_edit)
        
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(0, 100000)
        self.rate_spin.setPrefix("₹ ")
        self.rate_spin.setSuffix(" /hr")
        form.addRow("Hourly Rate:", self.rate_spin)
        
        self.color_combo = QComboBox()
        colors = [
            ("#6366f1", "Indigo"),
            ("#10b981", "Emerald"),
            ("#f59e0b", "Amber"),
            ("#ec4899", "Pink"),
            ("#8b5cf6", "Violet"),
            ("#3b82f6", "Blue"),
            ("#ef4444", "Red"),
            ("#14b8a6", "Teal")
        ]
        for color, name in colors:
            self.color_combo.addItem(f"● {name}", color)
        form.addRow("Color:", self.color_combo)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Project")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        # Load existing data
        if self.project:
            self.name_edit.setText(self.project.name)
            self.desc_edit.setText(self.project.description or "")
            self.rate_spin.setValue(int(self.project.hourly_rate))
            index = self.color_combo.findData(self.project.color)
            if index >= 0:
                self.color_combo.setCurrentIndex(index)
    
    def _save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Please enter a project name.")
            return
        
        session = get_session()
        
        if self.project:
            project = session.query(Project).get(self.project.id)
        else:
            project = Project()
            session.add(project)
        
        project.name = name
        project.description = self.desc_edit.toPlainText().strip() or None
        project.hourly_rate = float(self.rate_spin.value())
        project.color = self.color_combo.currentData()
        
        session.commit()
        session.close()
        
        self.accept()


class ManualEntryDialog(QDialog):
    """Dialog for manual time entry"""
    
    def __init__(self, projects: List[Project], parent=None):
        super().__init__(parent)
        self.projects = projects
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Add Manual Entry")
        self.setMinimumWidth(450)
        self.setStyleSheet("""
            QDialog {
                background-color: #1f2937;
            }
            QLabel {
                color: #e5e7eb;
            }
            QLineEdit, QTextEdit, QDateTimeEdit, QSpinBox, QComboBox {
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
            QCheckBox {
                color: #e5e7eb;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        self.project_combo = QComboBox()
        self.project_combo.addItem("No Project", None)
        for project in self.projects:
            self.project_combo.addItem(f"● {project.name}", project.id)
        form.addRow("Project:", self.project_combo)
        
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("What were you working on?")
        form.addRow("Description:", self.desc_edit)
        
        self.start_edit = QDateTimeEdit()
        self.start_edit.setDateTime(QDateTime.currentDateTime().addSecs(-3600))
        self.start_edit.setCalendarPopup(True)
        form.addRow("Start Time:", self.start_edit)
        
        self.end_edit = QDateTimeEdit()
        self.end_edit.setDateTime(QDateTime.currentDateTime())
        self.end_edit.setCalendarPopup(True)
        form.addRow("End Time:", self.end_edit)
        
        self.billable_check = QCheckBox("Billable time")
        self.billable_check.setChecked(True)
        form.addRow("", self.billable_check)
        
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("coding, meetings, research (comma separated)")
        form.addRow("Tags:", self.tags_edit)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Add Entry")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _save(self):
        start = self.start_edit.dateTime().toPyDateTime()
        end = self.end_edit.dateTime().toPyDateTime()
        
        if end <= start:
            QMessageBox.warning(self, "Validation", "End time must be after start time.")
            return
        
        duration = int((end - start).total_seconds() / 60)
        
        session = get_session()
        
        entry = TimeEntry(
            project_id=self.project_combo.currentData(),
            description=self.desc_edit.text().strip() or None,
            start_time=start,
            end_time=end,
            duration_minutes=duration,
            is_manual=True,
            billable=self.billable_check.isChecked(),
            tags=[t.strip() for t in self.tags_edit.text().split(",") if t.strip()]
        )
        
        session.add(entry)
        session.commit()
        session.close()
        
        self.accept()


class TimeTrackerModule(QWidget):
    """Time Tracker Module"""
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer_tick)
        self._start_time: Optional[datetime] = None
        self._elapsed_seconds = 0
        self._current_project: Optional[Project] = None
        self._is_running = False
        
        self._setup_ui()
        self._load_entries()
    
    def _setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("⏱️ Time Tracker")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f9fafb;
            }
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Manual entry button
        manual_btn = QPushButton("+ Manual Entry")
        manual_btn.setStyleSheet("""
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
        """)
        manual_btn.clicked.connect(self._show_manual_entry)
        header_layout.addWidget(manual_btn)
        
        layout.addLayout(header_layout)
        
        # Main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Timer
        self.left_panel = QFrame(self)
        self.left_panel.setStyleSheet("""
            QFrame {
                background-color: transparent;
            }
        """)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 16, 0)
        
        # Timer display
        self.timer_display = TimerDisplay()
        left_layout.addWidget(self.timer_display)
        
        # Project selector
        self.project_frame = QFrame(self)
        self.project_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 8px;
                border: 1px solid #374151;
                padding: 12px;
            }
        """)
        project_layout = QVBoxLayout(self.project_frame)
        
        project_label = QLabel("Project")
        project_label.setStyleSheet("color: #9ca3af; font-size: 12px;")
        project_layout.addWidget(project_label)
        
        self.project_selector = ProjectSelector()
        self.project_selector.project_selected.connect(self._on_project_selected)
        self.project_selector.add_requested.connect(self._show_add_project)
        self.project_selector.load_projects()
        project_layout.addWidget(self.project_selector)
        
        left_layout.addWidget(self.project_frame)
        
        # Description input
        self.desc_frame = QFrame(self)
        self.desc_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 8px;
                border: 1px solid #374151;
                padding: 12px;
            }
        """)
        desc_layout = QVBoxLayout(self.desc_frame)
        
        desc_label = QLabel("Description")
        desc_label.setStyleSheet("color: #9ca3af; font-size: 12px;")
        desc_layout.addWidget(desc_label)
        
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("What are you working on?")
        self.desc_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 10px;
                color: #e5e7eb;
                font-size: 13px;
            }
        """)
        desc_layout.addWidget(self.desc_edit)
        
        left_layout.addWidget(self.desc_frame)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 8px;
                padding: 14px 28px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.start_btn.clicked.connect(self._toggle_timer)
        btn_layout.addWidget(self.start_btn)
        
        self.reset_btn = QPushButton("⟳ Reset")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 8px;
                padding: 14px 20px;
                color: #e5e7eb;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        self.reset_btn.clicked.connect(self._reset_timer)
        btn_layout.addWidget(self.reset_btn)
        
        left_layout.addLayout(btn_layout)
        left_layout.addStretch()
        
        splitter.addWidget(self.left_panel)
        
        # Right panel - Time entries
        self.right_panel = QFrame(self)
        self.right_panel.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)
        
        # Tabs for Today/Week/Month
        tabs = QTabWidget()
        tabs.setStyleSheet("""
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
        
        # Today tab
        self.today_table = self._create_entries_table()
        tabs.addTab(self.today_table, "Today")
        
        # This week tab
        self.week_table = self._create_entries_table()
        tabs.addTab(self.week_table, "This Week")
        
        # This month tab
        self.month_table = self._create_entries_table()
        tabs.addTab(self.month_table, "This Month")
        
        right_layout.addWidget(tabs)
        
        # Summary stats
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("""
            QLabel {
                color: #9ca3af;
                font-size: 12px;
                padding: 8px;
            }
        """)
        right_layout.addWidget(self.stats_label)
        
        splitter.addWidget(self.right_panel)
        splitter.setSizes([350, 600])
        
        layout.addWidget(splitter, 1)
    
    def _create_entries_table(self) -> QTableWidget:
        """Create a time entries table"""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Project", "Description", "Duration", "Date", "Actions"])
        table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #374151;
                color: #9ca3af;
                border: none;
                padding: 8px;
                font-weight: 500;
            }
        """)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                gridline-color: #374151;
            }
            QTableWidget::item {
                color: #e5e7eb;
                padding: 8px;
            }
            QTableWidget::item:alternate {
                background-color: rgba(255, 255, 255, 0.02);
            }
            QTableWidget::item:selected {
                background-color: rgba(99, 102, 241, 0.2);
            }
        """)
        
        return table
    
    def _toggle_timer(self):
        """Start or stop the timer"""
        if self._is_running:
            self._stop_timer()
        else:
            self._start_timer()
    
    def _start_timer(self):
        """Start the timer"""
        self._start_time = datetime.now()
        self._is_running = True
        self._timer.start(1000)
        
        self.start_btn.setText("⏹ Stop")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                border: none;
                border-radius: 8px;
                padding: 14px 28px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        
        project_name = self._current_project.name if self._current_project else "No project"
        self.timer_display.set_status(f"Tracking: {project_name}", "#10b981")
        self.timer_display.set_running(True)
    
    def _stop_timer(self):
        """Stop the timer and save entry"""
        self._timer.stop()
        self._is_running = False
        
        # Save entry
        if self._start_time and self._elapsed_seconds > 60:  # Min 1 minute
            session = get_session()
            entry = TimeEntry(
                project_id=self._current_project.id if self._current_project else None,
                description=self.desc_edit.text().strip() or None,
                start_time=self._start_time,
                end_time=datetime.now(),
                duration_minutes=self._elapsed_seconds // 60,
                is_manual=False,
                billable=True
            )
            session.add(entry)
            session.commit()
            session.close()
            
            self._load_entries()
        
        self._reset_timer()
    
    def _reset_timer(self):
        """Reset the timer"""
        self._timer.stop()
        self._is_running = False
        self._start_time = None
        self._elapsed_seconds = 0
        
        self.start_btn.setText("▶ Start")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 8px;
                padding: 14px 28px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        
        self.timer_display.update_time(0)
        self.timer_display.set_status("Ready to track", "#6b7280")
        self.timer_display.set_running(False)
    
    def _on_timer_tick(self):
        """Timer tick handler"""
        if self._start_time:
            self._elapsed_seconds = int((datetime.now() - self._start_time).total_seconds())
            self.timer_display.update_time(self._elapsed_seconds)
    
    def _on_project_selected(self, project: Optional[Project]):
        """Handle project selection"""
        self._current_project = project
    
    def _show_add_project(self):
        """Show add project dialog"""
        dialog = ProjectDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.project_selector.load_projects()
    
    def _show_manual_entry(self):
        """Show manual entry dialog"""
        session = get_session()
        projects = session.query(Project).filter(Project.is_active == True).all()
        session.close()
        
        dialog = ManualEntryDialog(projects, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_entries()
    
    def _load_entries(self):
        """Load time entries into tables"""
        session = get_session()
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Today
        today_entries = session.query(TimeEntry).filter(
            TimeEntry.start_time >= today
        ).order_by(TimeEntry.start_time.desc()).all()
        self._populate_table(self.today_table, today_entries, session)
        
        # Week
        week_entries = session.query(TimeEntry).filter(
            TimeEntry.start_time >= week_start
        ).order_by(TimeEntry.start_time.desc()).all()
        self._populate_table(self.week_table, week_entries, session)
        
        # Month
        month_entries = session.query(TimeEntry).filter(
            TimeEntry.start_time >= month_start
        ).order_by(TimeEntry.start_time.desc()).all()
        self._populate_table(self.month_table, month_entries, session)
        
        # Update stats
        total_today = sum(e.duration_minutes for e in today_entries)
        total_week = sum(e.duration_minutes for e in week_entries)
        total_month = sum(e.duration_minutes for e in month_entries)
        
        self.stats_label.setText(
            f"Today: {total_today // 60}h {total_today % 60}m | "
            f"Week: {total_week // 60}h {total_week % 60}m | "
            f"Month: {total_month // 60}h {total_month % 60}m"
        )
        
        session.close()
    
    def _populate_table(self, table: QTableWidget, entries: List[TimeEntry], session):
        """Populate a table with entries"""
        table.setRowCount(len(entries))
        
        for row, entry in enumerate(entries):
            # Project
            project_name = "No Project"
            if entry.project_id:
                project = session.query(Project).get(entry.project_id)
                if project:
                    project_name = project.name
            table.setItem(row, 0, QTableWidgetItem(project_name))
            
            # Description
            desc = entry.description or "-"
            table.setItem(row, 1, QTableWidgetItem(desc))
            
            # Duration
            hours = entry.duration_minutes // 60
            mins = entry.duration_minutes % 60
            duration = f"{hours}h {mins}m" if hours else f"{mins}m"
            table.setItem(row, 2, QTableWidgetItem(duration))
            
            # Date
            date_str = entry.start_time.strftime("%d %b %H:%M")
            table.setItem(row, 3, QTableWidgetItem(date_str))
            
            # Actions
            delete_btn = QPushButton("🗑️")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    padding: 4px;
                }
                QPushButton:hover {
                    background-color: rgba(239, 68, 68, 0.2);
                }
            """)
            delete_btn.clicked.connect(lambda checked, eid=entry.id: self._delete_entry(eid))
            table.setCellWidget(row, 4, delete_btn)
    
    def _delete_entry(self, entry_id: int):
        """Delete a time entry"""
        reply = QMessageBox.question(
            self, "Delete Entry",
            "Are you sure you want to delete this time entry?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            session = get_session()
            entry = session.query(TimeEntry).get(entry_id)
            if entry:
                session.delete(entry)
                session.commit()
            session.close()
            self._load_entries()

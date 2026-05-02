"""
Environment Manager Module - Manage environment variables and profiles
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QPushButton, QLineEdit, QTextEdit,
    QListWidget, QListWidgetItem, QTabWidget, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QInputDialog, QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime
import os
import json

Base = declarative_base()


class EnvProfile(Base):
    """Environment profile model"""
    __tablename__ = 'env_profiles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    variables = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EnvManagerModule(QWidget):
    """Environment Manager Module"""
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        
        # Create table if needed
        Base.metadata.create_all(db._engine)
        
        self._setup_ui()
        self._load_profiles()
        self._load_system_env()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        title = QLabel("🌐 Environment Manager")
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
        
        # System tab
        system_tab = self._create_system_tab()
        tabs.addTab(system_tab, "💻 System Variables")
        
        # Profiles tab
        profiles_tab = self._create_profiles_tab()
        tabs.addTab(profiles_tab, "📁 Profiles")
        
        # .env Editor tab
        env_editor_tab = self._create_env_editor_tab()
        tabs.addTab(env_editor_tab, "📝 .env Editor")
        
        layout.addWidget(tabs, 1)
    
    def _create_system_tab(self):
        """Create system variables tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        
        self.sys_search = QLineEdit()
        self.sys_search.setPlaceholderText("Filter variables...")
        self.sys_search.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 10px;
                color: #e5e7eb;
            }
        """)
        self.sys_search.textChanged.connect(self._filter_system_env)
        search_layout.addWidget(self.sys_search)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
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
        refresh_btn.clicked.connect(self._load_system_env)
        search_layout.addWidget(refresh_btn)
        
        layout.addLayout(search_layout)
        
        # Table
        self.sys_table = QTableWidget()
        self.sys_table.setColumnCount(2)
        self.sys_table.setHorizontalHeaderLabels(["Variable", "Value"])
        self.sys_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.sys_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.sys_table.setColumnWidth(0, 250)
        self.sys_table.setStyleSheet("""
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
                padding: 10px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.sys_table)
        
        return widget
    
    def _create_profiles_tab(self):
        """Create profiles tab"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Left: Profile list
        self.profile_left_frame = QFrame(self)
        self.profile_left_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
            }
        """)
        self.profile_left_frame.setFixedWidth(250)
        left_layout = QVBoxLayout(self.profile_left_frame)
        left_layout.setContentsMargins(12, 12, 12, 12)
        
        left_layout.addWidget(QLabel("Profiles"))
        
        self.profile_list = QListWidget()
        self.profile_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                color: #e5e7eb;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #374151;
            }
            QListWidget::item:hover {
                background-color: #1f2937;
            }
        """)
        self.profile_list.currentRowChanged.connect(self._on_profile_selected)
        left_layout.addWidget(self.profile_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕")
        add_btn.setToolTip("New Profile")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        add_btn.clicked.connect(self._add_profile)
        btn_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setToolTip("Delete Profile")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        delete_btn.clicked.connect(self._delete_profile)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)
        
        layout.addWidget(self.profile_left_frame)
        
        # Right: Profile editor
        self.profile_right_frame = QFrame(self)
        self.profile_right_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
            }
        """)
        right_layout = QVBoxLayout(self.profile_right_frame)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)
        
        # Profile name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Profile Name:"))
        self.profile_name = QLineEdit()
        self.profile_name.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 10px;
                color: #e5e7eb;
            }
        """)
        name_layout.addWidget(self.profile_name)
        right_layout.addLayout(name_layout)
        
        # Variables table
        right_layout.addWidget(QLabel("Variables:"))
        
        self.profile_table = QTableWidget()
        self.profile_table.setColumnCount(2)
        self.profile_table.setHorizontalHeaderLabels(["Key", "Value"])
        self.profile_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.profile_table.setStyleSheet("""
            QTableWidget {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 8px;
                gridline-color: #374151;
                color: #e5e7eb;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #374151;
                color: #9ca3af;
                border: none;
                padding: 8px;
            }
        """)
        right_layout.addWidget(self.profile_table)
        
        # Variable buttons
        var_btn_layout = QHBoxLayout()
        
        add_var_btn = QPushButton("➕ Add Variable")
        add_var_btn.setStyleSheet("""
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
        add_var_btn.clicked.connect(self._add_variable)
        var_btn_layout.addWidget(add_var_btn)
        
        remove_var_btn = QPushButton("🗑️ Remove")
        remove_var_btn.setStyleSheet("""
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
        remove_var_btn.clicked.connect(self._remove_variable)
        var_btn_layout.addWidget(remove_var_btn)
        
        var_btn_layout.addStretch()
        
        save_btn = QPushButton("💾 Save Profile")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        save_btn.clicked.connect(self._save_profile)
        var_btn_layout.addWidget(save_btn)
        
        export_btn = QPushButton("📤 Export .env")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        export_btn.clicked.connect(self._export_env)
        var_btn_layout.addWidget(export_btn)
        
        right_layout.addLayout(var_btn_layout)
        
        layout.addWidget(self.profile_right_frame, 1)
        
        return widget
    
    def _create_env_editor_tab(self):
        """Create .env file editor tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # File selection
        file_layout = QHBoxLayout()
        
        self.env_file_path = QLineEdit()
        self.env_file_path.setPlaceholderText("Select .env file or enter path...")
        self.env_file_path.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 10px;
                color: #e5e7eb;
            }
        """)
        file_layout.addWidget(self.env_file_path)
        
        browse_btn = QPushButton("📂 Browse")
        browse_btn.setStyleSheet("""
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
        browse_btn.clicked.connect(self._browse_env_file)
        file_layout.addWidget(browse_btn)
        
        load_btn = QPushButton("📥 Load")
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                color: white;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        load_btn.clicked.connect(self._load_env_file)
        file_layout.addWidget(load_btn)
        
        layout.addLayout(file_layout)
        
        # Editor
        self.env_editor = QTextEdit()
        self.env_editor.setPlaceholderText("# Environment Variables\n# KEY=value\n# DATABASE_URL=postgres://...")
        self.env_editor.setStyleSheet("""
            QTextEdit {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
                color: #e5e7eb;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.env_editor)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        save_file_btn = QPushButton("💾 Save File")
        save_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        save_file_btn.clicked.connect(self._save_env_file)
        btn_layout.addWidget(save_file_btn)
        
        parse_btn = QPushButton("🔍 Parse & Validate")
        parse_btn.setStyleSheet("""
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
        parse_btn.clicked.connect(self._parse_env_content)
        btn_layout.addWidget(parse_btn)
        
        btn_layout.addStretch()
        
        import_profile_btn = QPushButton("📥 Import from Profile")
        import_profile_btn.setStyleSheet("""
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
        import_profile_btn.clicked.connect(self._import_from_profile)
        btn_layout.addWidget(import_profile_btn)
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def _load_system_env(self):
        """Load system environment variables"""
        self.sys_table.setRowCount(0)
        
        for key, value in sorted(os.environ.items()):
            row = self.sys_table.rowCount()
            self.sys_table.insertRow(row)
            self.sys_table.setItem(row, 0, QTableWidgetItem(key))
            self.sys_table.setItem(row, 1, QTableWidgetItem(value))
        
        self._system_env_cache = dict(os.environ)
    
    def _filter_system_env(self, text: str):
        """Filter system env table"""
        text = text.lower()
        for row in range(self.sys_table.rowCount()):
            key = self.sys_table.item(row, 0).text().lower()
            value = self.sys_table.item(row, 1).text().lower()
            match = text in key or text in value
            self.sys_table.setRowHidden(row, not match)
    
    def _load_profiles(self):
        """Load profiles from database"""
        self.profile_list.clear()
        
        with self.db.session() as session:
            profiles = session.query(EnvProfile).order_by(EnvProfile.name).all()
            for profile in profiles:
                item = QListWidgetItem(f"📁 {profile.name}")
                item.setData(Qt.ItemDataRole.UserRole, profile.id)
                self.profile_list.addItem(item)
    
    def _on_profile_selected(self, row: int):
        """Handle profile selection"""
        if row < 0:
            return
        
        item = self.profile_list.item(row)
        profile_id = item.data(Qt.ItemDataRole.UserRole)
        
        with self.db.session() as session:
            profile = session.query(EnvProfile).filter_by(id=profile_id).first()
            if profile:
                self.profile_name.setText(profile.name)
                
                # Load variables
                self.profile_table.setRowCount(0)
                try:
                    variables = json.loads(profile.variables or "{}")
                    for key, value in variables.items():
                        row = self.profile_table.rowCount()
                        self.profile_table.insertRow(row)
                        self.profile_table.setItem(row, 0, QTableWidgetItem(key))
                        self.profile_table.setItem(row, 1, QTableWidgetItem(value))
                except json.JSONDecodeError:
                    pass
    
    def _add_profile(self):
        """Add new profile"""
        name, ok = QInputDialog.getText(self, "New Profile", "Profile name:")
        if ok and name:
            with self.db.session() as session:
                profile = EnvProfile(name=name, variables="{}")
                session.add(profile)
                session.commit()
            
            self._load_profiles()
    
    def _delete_profile(self):
        """Delete selected profile"""
        item = self.profile_list.currentItem()
        if not item:
            return
        
        reply = QMessageBox.question(
            self, "Delete Profile",
            f"Delete profile '{item.text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            profile_id = item.data(Qt.ItemDataRole.UserRole)
            with self.db.session() as session:
                session.query(EnvProfile).filter_by(id=profile_id).delete()
                session.commit()
            
            self._load_profiles()
            self.profile_name.clear()
            self.profile_table.setRowCount(0)
    
    def _add_variable(self):
        """Add variable row"""
        row = self.profile_table.rowCount()
        self.profile_table.insertRow(row)
        self.profile_table.setItem(row, 0, QTableWidgetItem(""))
        self.profile_table.setItem(row, 1, QTableWidgetItem(""))
    
    def _remove_variable(self):
        """Remove selected variable"""
        row = self.profile_table.currentRow()
        if row >= 0:
            self.profile_table.removeRow(row)
    
    def _save_profile(self):
        """Save current profile"""
        item = self.profile_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Error", "No profile selected")
            return
        
        profile_id = item.data(Qt.ItemDataRole.UserRole)
        name = self.profile_name.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Error", "Profile name required")
            return
        
        # Collect variables
        variables = {}
        for row in range(self.profile_table.rowCount()):
            key_item = self.profile_table.item(row, 0)
            value_item = self.profile_table.item(row, 1)
            if key_item and key_item.text().strip():
                key = key_item.text().strip()
                value = value_item.text() if value_item else ""
                variables[key] = value
        
        with self.db.session() as session:
            profile = session.query(EnvProfile).filter_by(id=profile_id).first()
            if profile:
                profile.name = name
                profile.variables = json.dumps(variables)
                session.commit()
        
        self._load_profiles()
        QMessageBox.information(self, "Saved", "Profile saved successfully")
    
    def _export_env(self):
        """Export profile as .env file"""
        lines = []
        for row in range(self.profile_table.rowCount()):
            key_item = self.profile_table.item(row, 0)
            value_item = self.profile_table.item(row, 1)
            if key_item and key_item.text().strip():
                key = key_item.text().strip()
                value = value_item.text() if value_item else ""
                # Quote value if it contains spaces
                if " " in value:
                    value = f'"{value}"'
                lines.append(f"{key}={value}")
        
        content = "\n".join(lines)
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Save .env File", ".env", "Environment Files (*.env);;All Files (*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Exported", f"Exported to {path}")
    
    def _browse_env_file(self):
        """Browse for .env file"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open .env File", "", "Environment Files (*.env);;All Files (*)"
        )
        if path:
            self.env_file_path.setText(path)
            self._load_env_file()
    
    def _load_env_file(self):
        """Load .env file content"""
        path = self.env_file_path.text().strip()
        if not path:
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.env_editor.setText(content)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load file: {e}")
    
    def _save_env_file(self):
        """Save .env file"""
        path = self.env_file_path.text().strip()
        if not path:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save .env File", ".env", "Environment Files (*.env)"
            )
            if path:
                self.env_file_path.setText(path)
            else:
                return
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.env_editor.toPlainText())
            QMessageBox.information(self, "Saved", f"Saved to {path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save: {e}")
    
    def _parse_env_content(self):
        """Parse and validate .env content"""
        content = self.env_editor.toPlainText()
        lines = content.split("\n")
        
        valid = 0
        invalid = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            if "=" in line:
                valid += 1
            else:
                invalid.append(f"Line {i}: {line[:30]}...")
        
        if invalid:
            msg = f"Found {valid} valid variable(s)\n\nInvalid lines:\n" + "\n".join(invalid[:5])
            if len(invalid) > 5:
                msg += f"\n...and {len(invalid) - 5} more"
        else:
            msg = f"✓ All {valid} variable(s) are valid"
        
        QMessageBox.information(self, "Validation Result", msg)
    
    def _import_from_profile(self):
        """Import profile into editor"""
        with self.db.session() as session:
            profiles = session.query(EnvProfile).order_by(EnvProfile.name).all()
            names = [p.name for p in profiles]
        
        if not names:
            QMessageBox.warning(self, "Error", "No profiles available")
            return
        
        name, ok = QInputDialog.getItem(
            self, "Select Profile", "Import variables from:", names, 0, False
        )
        
        if ok:
            with self.db.session() as session:
                profile = session.query(EnvProfile).filter_by(name=name).first()
                if profile:
                    try:
                        variables = json.loads(profile.variables or "{}")
                        lines = [f"{k}={v}" for k, v in variables.items()]
                        self.env_editor.setText("\n".join(lines))
                    except json.JSONDecodeError:
                        pass

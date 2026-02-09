"""
Finance Module - Client management, invoicing, and expense tracking
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QLineEdit, QTextEdit,
    QListWidget, QListWidgetItem, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QBrush
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import json

Base = declarative_base()


class Client(Base):
    """Client model"""
    __tablename__ = 'finance_clients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200))
    phone = Column(String(50))
    address = Column(Text)
    company = Column(String(200))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Invoice(Base):
    """Invoice model"""
    __tablename__ = 'finance_invoices'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('finance_clients.id'))
    invoice_number = Column(String(50), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    items = Column(Text)  # JSON string
    subtotal = Column(Float, default=0)
    tax_rate = Column(Float, default=0)
    total = Column(Float, default=0)
    status = Column(String(20), default='draft')  # draft, sent, paid
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Expense(Base):
    """Expense model"""
    __tablename__ = 'finance_expenses'
    
    id = Column(Integer, primary_key=True)
    description = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(100))
    date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class FinanceModule(QWidget):
    """Finance Module"""
    
    EXPENSE_CATEGORIES = [
        "Software", "Hardware", "Office", "Travel", 
        "Marketing", "Utilities", "Services", "Other"
    ]
    
    def __init__(self, db, config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        
        # Create tables
        Base.metadata.create_all(db._engine)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("💰 Finance Manager")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f9fafb;
            }
        """)
        header.addWidget(title)
        header.addStretch()
        
        # Summary cards
        self.summary_frame = QFrame()
        self.summary_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 8px;
                border: 1px solid #374151;
            }
        """)
        summary_layout = QHBoxLayout(self.summary_frame)
        summary_layout.setContentsMargins(12, 8, 12, 8)
        summary_layout.setSpacing(24)
        
        self.clients_count = QLabel("0 Clients")
        self.clients_count.setStyleSheet("color: #60a5fa; font-weight: bold;")
        summary_layout.addWidget(self.clients_count)
        
        self.invoices_total = QLabel("$0 Invoiced")
        self.invoices_total.setStyleSheet("color: #10b981; font-weight: bold;")
        summary_layout.addWidget(self.invoices_total)
        
        self.expenses_total = QLabel("$0 Expenses")
        self.expenses_total.setStyleSheet("color: #f59e0b; font-weight: bold;")
        summary_layout.addWidget(self.expenses_total)
        
        header.addWidget(self.summary_frame)
        layout.addLayout(header)
        
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
        
        # Clients tab
        clients_tab = self._create_clients_tab()
        tabs.addTab(clients_tab, "👥 Clients")
        
        # Invoices tab
        invoices_tab = self._create_invoices_tab()
        tabs.addTab(invoices_tab, "📄 Invoices")
        
        # Expenses tab
        expenses_tab = self._create_expenses_tab()
        tabs.addTab(expenses_tab, "💸 Expenses")
        
        layout.addWidget(tabs, 1)
    
    def _create_clients_tab(self):
        """Create clients management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add Client")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        add_btn.clicked.connect(self._add_client)
        toolbar.addWidget(add_btn)
        
        toolbar.addStretch()
        
        self.client_search = QLineEdit()
        self.client_search.setPlaceholderText("Search clients...")
        self.client_search.setFixedWidth(250)
        self.client_search.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 8px;
                color: #e5e7eb;
            }
        """)
        self.client_search.textChanged.connect(self._filter_clients)
        toolbar.addWidget(self.client_search)
        
        layout.addLayout(toolbar)
        
        # Clients table
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(6)
        self.clients_table.setHorizontalHeaderLabels(["Name", "Email", "Phone", "Company", "Invoices", "Actions"])
        self.clients_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.clients_table.setStyleSheet("""
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
        layout.addWidget(self.clients_table)
        
        return widget
    
    def _create_invoices_tab(self):
        """Create invoices tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton("➕ New Invoice")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        add_btn.clicked.connect(self._create_invoice)
        toolbar.addWidget(add_btn)
        
        toolbar.addStretch()
        
        # Status filter
        toolbar.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Draft", "Sent", "Paid"])
        self.status_filter.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
            }
        """)
        self.status_filter.currentTextChanged.connect(self._filter_invoices)
        toolbar.addWidget(self.status_filter)
        
        layout.addLayout(toolbar)
        
        # Invoices table
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(7)
        self.invoices_table.setHorizontalHeaderLabels(["#", "Client", "Date", "Due Date", "Total", "Status", "Actions"])
        self.invoices_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.invoices_table.setStyleSheet("""
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
        layout.addWidget(self.invoices_table)
        
        return widget
    
    def _create_expenses_tab(self):
        """Create expenses tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add Expense")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d97706;
            }
        """)
        add_btn.clicked.connect(self._add_expense)
        toolbar.addWidget(add_btn)
        
        toolbar.addStretch()
        
        # Category filter
        toolbar.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItems(["All"] + self.EXPENSE_CATEGORIES)
        self.category_filter.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 8px;
                color: #e5e7eb;
            }
        """)
        self.category_filter.currentTextChanged.connect(self._filter_expenses)
        toolbar.addWidget(self.category_filter)
        
        layout.addLayout(toolbar)
        
        # Expenses table
        self.expenses_table = QTableWidget()
        self.expenses_table.setColumnCount(5)
        self.expenses_table.setHorizontalHeaderLabels(["Date", "Description", "Category", "Amount", "Actions"])
        self.expenses_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.expenses_table.setStyleSheet("""
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
        layout.addWidget(self.expenses_table)
        
        return widget
    
    def _load_data(self):
        """Load all data"""
        self._load_clients()
        self._load_invoices()
        self._load_expenses()
        self._update_summary()
    
    def _load_clients(self):
        """Load clients into table"""
        self.clients_table.setRowCount(0)
        
        with self.db.session() as session:
            clients = session.query(Client).order_by(Client.name).all()
            
            for client in clients:
                row = self.clients_table.rowCount()
                self.clients_table.insertRow(row)
                
                self.clients_table.setItem(row, 0, QTableWidgetItem(client.name))
                self.clients_table.setItem(row, 1, QTableWidgetItem(client.email or ""))
                self.clients_table.setItem(row, 2, QTableWidgetItem(client.phone or ""))
                self.clients_table.setItem(row, 3, QTableWidgetItem(client.company or ""))
                
                # Invoice count
                inv_count = session.query(Invoice).filter_by(client_id=client.id).count()
                self.clients_table.setItem(row, 4, QTableWidgetItem(str(inv_count)))
                
                # Actions
                actions = QWidget()
                actions_layout = QHBoxLayout(actions)
                actions_layout.setContentsMargins(4, 4, 4, 4)
                actions_layout.setSpacing(4)
                
                edit_btn = QPushButton("✏️")
                edit_btn.setFixedSize(28, 28)
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #374151;
                        border: none;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #4b5563;
                    }
                """)
                client_id = client.id
                edit_btn.clicked.connect(lambda _, cid=client_id: self._edit_client(cid))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("🗑️")
                delete_btn.setFixedSize(28, 28)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #374151;
                        border: none;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #ef4444;
                    }
                """)
                delete_btn.clicked.connect(lambda _, cid=client_id: self._delete_client(cid))
                actions_layout.addWidget(delete_btn)
                
                self.clients_table.setCellWidget(row, 5, actions)
    
    def _load_invoices(self):
        """Load invoices into table"""
        self.invoices_table.setRowCount(0)
        
        status_filter = self.status_filter.currentText().lower()
        
        with self.db.session() as session:
            query = session.query(Invoice).order_by(Invoice.date.desc())
            
            if status_filter != "all":
                query = query.filter(Invoice.status == status_filter)
            
            invoices = query.all()
            
            for invoice in invoices:
                row = self.invoices_table.rowCount()
                self.invoices_table.insertRow(row)
                
                self.invoices_table.setItem(row, 0, QTableWidgetItem(invoice.invoice_number))
                
                # Client name
                client = session.query(Client).filter_by(id=invoice.client_id).first()
                client_name = client.name if client else "Unknown"
                self.invoices_table.setItem(row, 1, QTableWidgetItem(client_name))
                
                # Dates
                date_str = invoice.date.strftime("%Y-%m-%d") if invoice.date else ""
                self.invoices_table.setItem(row, 2, QTableWidgetItem(date_str))
                
                due_str = invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else ""
                self.invoices_table.setItem(row, 3, QTableWidgetItem(due_str))
                
                # Total
                self.invoices_table.setItem(row, 4, QTableWidgetItem(f"${invoice.total:.2f}"))
                
                # Status with color
                status_item = QTableWidgetItem(invoice.status.title())
                if invoice.status == "paid":
                    status_item.setForeground(QBrush(QColor("#10b981")))
                elif invoice.status == "sent":
                    status_item.setForeground(QBrush(QColor("#60a5fa")))
                else:
                    status_item.setForeground(QBrush(QColor("#9ca3af")))
                self.invoices_table.setItem(row, 5, status_item)
                
                # Actions
                actions = QWidget()
                actions_layout = QHBoxLayout(actions)
                actions_layout.setContentsMargins(4, 4, 4, 4)
                actions_layout.setSpacing(4)
                
                view_btn = QPushButton("👁️")
                view_btn.setFixedSize(28, 28)
                view_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #374151;
                        border: none;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #4b5563;
                    }
                """)
                inv_id = invoice.id
                view_btn.clicked.connect(lambda _, iid=inv_id: self._view_invoice(iid))
                actions_layout.addWidget(view_btn)
                
                delete_btn = QPushButton("🗑️")
                delete_btn.setFixedSize(28, 28)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #374151;
                        border: none;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #ef4444;
                    }
                """)
                delete_btn.clicked.connect(lambda _, iid=inv_id: self._delete_invoice(iid))
                actions_layout.addWidget(delete_btn)
                
                self.invoices_table.setCellWidget(row, 6, actions)
    
    def _load_expenses(self):
        """Load expenses into table"""
        self.expenses_table.setRowCount(0)
        
        category = self.category_filter.currentText()
        
        with self.db.session() as session:
            query = session.query(Expense).order_by(Expense.date.desc())
            
            if category != "All":
                query = query.filter(Expense.category == category)
            
            expenses = query.all()
            
            for expense in expenses:
                row = self.expenses_table.rowCount()
                self.expenses_table.insertRow(row)
                
                date_str = expense.date.strftime("%Y-%m-%d") if expense.date else ""
                self.expenses_table.setItem(row, 0, QTableWidgetItem(date_str))
                self.expenses_table.setItem(row, 1, QTableWidgetItem(expense.description))
                self.expenses_table.setItem(row, 2, QTableWidgetItem(expense.category or ""))
                
                amount_item = QTableWidgetItem(f"${expense.amount:.2f}")
                amount_item.setForeground(QBrush(QColor("#f59e0b")))
                self.expenses_table.setItem(row, 3, amount_item)
                
                # Actions
                delete_btn = QPushButton("🗑️")
                delete_btn.setFixedSize(28, 28)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #374151;
                        border: none;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #ef4444;
                    }
                """)
                exp_id = expense.id
                delete_btn.clicked.connect(lambda _, eid=exp_id: self._delete_expense(eid))
                self.expenses_table.setCellWidget(row, 4, delete_btn)
    
    def _update_summary(self):
        """Update summary cards"""
        with self.db.session() as session:
            clients_count = session.query(Client).count()
            self.clients_count.setText(f"📋 {clients_count} Clients")
            
            invoices_total = session.query(Invoice).filter_by(status='paid').all()
            total = sum(inv.total for inv in invoices_total)
            self.invoices_total.setText(f"💵 ${total:,.2f} Invoiced")
            
            expenses = session.query(Expense).all()
            expenses_total = sum(exp.amount for exp in expenses)
            self.expenses_total.setText(f"💸 ${expenses_total:,.2f} Expenses")
    
    def _filter_clients(self, text: str):
        """Filter clients table"""
        text = text.lower()
        for row in range(self.clients_table.rowCount()):
            match = False
            for col in range(4):
                item = self.clients_table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.clients_table.setRowHidden(row, not match)
    
    def _filter_invoices(self, status: str):
        """Filter invoices"""
        self._load_invoices()
    
    def _filter_expenses(self, category: str):
        """Filter expenses"""
        self._load_expenses()
    
    def _add_client(self):
        """Add new client"""
        dialog = ClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            with self.db.session() as session:
                client = Client(**data)
                session.add(client)
                session.commit()
            self._load_clients()
            self._update_summary()
    
    def _edit_client(self, client_id: int):
        """Edit existing client"""
        with self.db.session() as session:
            client = session.query(Client).filter_by(id=client_id).first()
            if client:
                dialog = ClientDialog(self, client)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    data = dialog.get_data()
                    for key, value in data.items():
                        setattr(client, key, value)
                    session.commit()
                self._load_clients()
    
    def _delete_client(self, client_id: int):
        """Delete client"""
        reply = QMessageBox.question(
            self, "Delete Client",
            "Delete this client? This will not delete associated invoices.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            with self.db.session() as session:
                session.query(Client).filter_by(id=client_id).delete()
                session.commit()
            self._load_clients()
            self._update_summary()
    
    def _create_invoice(self):
        """Create new invoice"""
        dialog = InvoiceDialog(self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            with self.db.session() as session:
                invoice = Invoice(**data)
                session.add(invoice)
                session.commit()
            self._load_invoices()
            self._update_summary()
    
    def _view_invoice(self, invoice_id: int):
        """View invoice details"""
        with self.db.session() as session:
            invoice = session.query(Invoice).filter_by(id=invoice_id).first()
            if invoice:
                dialog = InvoiceDialog(self.db, self, invoice)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    data = dialog.get_data()
                    for key, value in data.items():
                        setattr(invoice, key, value)
                    session.commit()
                self._load_invoices()
                self._update_summary()
    
    def _delete_invoice(self, invoice_id: int):
        """Delete invoice"""
        reply = QMessageBox.question(
            self, "Delete Invoice",
            "Delete this invoice?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            with self.db.session() as session:
                session.query(Invoice).filter_by(id=invoice_id).delete()
                session.commit()
            self._load_invoices()
            self._update_summary()
    
    def _add_expense(self):
        """Add new expense"""
        dialog = ExpenseDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            with self.db.session() as session:
                expense = Expense(**data)
                session.add(expense)
                session.commit()
            self._load_expenses()
            self._update_summary()
    
    def _delete_expense(self, expense_id: int):
        """Delete expense"""
        reply = QMessageBox.question(
            self, "Delete Expense",
            "Delete this expense?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            with self.db.session() as session:
                session.query(Expense).filter_by(id=expense_id).delete()
                session.commit()
            self._load_expenses()
            self._update_summary()


class ClientDialog(QDialog):
    """Dialog for adding/editing clients"""
    
    def __init__(self, parent=None, client=None):
        super().__init__(parent)
        self.client = client
        self._setup_ui()
        
        if client:
            self._load_client()
    
    def _setup_ui(self):
        self.setWindowTitle("Client" if not self.client else "Edit Client")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: #1f2937;
            }
            QLabel {
                color: #e5e7eb;
            }
            QLineEdit, QTextEdit {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 8px;
                color: #e5e7eb;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Client name*")
        form.addRow("Name:", self.name_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@example.com")
        form.addRow("Email:", self.email_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+1 234 567 890")
        form.addRow("Phone:", self.phone_edit)
        
        self.company_edit = QLineEdit()
        form.addRow("Company:", self.company_edit)
        
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(60)
        form.addRow("Address:", self.address_edit)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        form.addRow("Notes:", self.notes_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _load_client(self):
        """Load client data into form"""
        self.name_edit.setText(self.client.name)
        self.email_edit.setText(self.client.email or "")
        self.phone_edit.setText(self.client.phone or "")
        self.company_edit.setText(self.client.company or "")
        self.address_edit.setText(self.client.address or "")
        self.notes_edit.setText(self.client.notes or "")
    
    def _validate_and_accept(self):
        """Validate and accept"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Error", "Name is required")
            return
        self.accept()
    
    def get_data(self) -> dict:
        """Get form data"""
        return {
            "name": self.name_edit.text().strip(),
            "email": self.email_edit.text().strip() or None,
            "phone": self.phone_edit.text().strip() or None,
            "company": self.company_edit.text().strip() or None,
            "address": self.address_edit.toPlainText().strip() or None,
            "notes": self.notes_edit.toPlainText().strip() or None,
        }


class InvoiceDialog(QDialog):
    """Dialog for creating/editing invoices"""
    
    def __init__(self, db, parent=None, invoice=None):
        super().__init__(parent)
        self.db = db
        self.invoice = invoice
        self._setup_ui()
        self._load_clients()
        
        if invoice:
            self._load_invoice()
    
    def _setup_ui(self):
        self.setWindowTitle("Invoice" if not self.invoice else "Edit Invoice")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #1f2937;
            }
            QLabel {
                color: #e5e7eb;
            }
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 8px;
                color: #e5e7eb;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        # Invoice number
        header.addWidget(QLabel("Invoice #:"))
        self.invoice_number = QLineEdit()
        self.invoice_number.setPlaceholderText("INV-001")
        if not self.invoice:
            self.invoice_number.setText(f"INV-{datetime.now().strftime('%Y%m%d%H%M')}")
        header.addWidget(self.invoice_number)
        
        # Client
        header.addWidget(QLabel("Client:"))
        self.client_combo = QComboBox()
        header.addWidget(self.client_combo, 1)
        
        layout.addLayout(header)
        
        # Dates and status
        dates = QHBoxLayout()
        
        dates.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        dates.addWidget(self.date_edit)
        
        dates.addWidget(QLabel("Due Date:"))
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setDate(QDate.currentDate().addDays(30))
        self.due_date_edit.setCalendarPopup(True)
        dates.addWidget(self.due_date_edit)
        
        dates.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Draft", "Sent", "Paid"])
        dates.addWidget(self.status_combo)
        
        layout.addLayout(dates)
        
        # Items table
        layout.addWidget(QLabel("Items:"))
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Description", "Qty", "Rate", "Amount"])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.items_table.setStyleSheet("""
            QTableWidget {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
                gridline-color: #374151;
                color: #e5e7eb;
            }
            QHeaderView::section {
                background-color: #1f2937;
                color: #9ca3af;
                border: none;
                padding: 8px;
            }
        """)
        layout.addWidget(self.items_table)
        
        # Item buttons
        item_btns = QHBoxLayout()
        add_item_btn = QPushButton("➕ Add Item")
        add_item_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px 12px;
                color: #e5e7eb;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        add_item_btn.clicked.connect(self._add_item_row)
        item_btns.addWidget(add_item_btn)
        
        remove_item_btn = QPushButton("🗑️ Remove")
        remove_item_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px 12px;
                color: #e5e7eb;
            }
            QPushButton:hover {
                background-color: #ef4444;
            }
        """)
        remove_item_btn.clicked.connect(self._remove_item_row)
        item_btns.addWidget(remove_item_btn)
        
        item_btns.addStretch()
        
        # Totals
        item_btns.addWidget(QLabel("Tax Rate %:"))
        self.tax_rate = QDoubleSpinBox()
        self.tax_rate.setRange(0, 100)
        self.tax_rate.setValue(0)
        self.tax_rate.valueChanged.connect(self._calculate_totals)
        item_btns.addWidget(self.tax_rate)
        
        self.total_label = QLabel("Total: $0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        item_btns.addWidget(self.total_label)
        
        layout.addLayout(item_btns)
        
        # Notes
        layout.addWidget(QLabel("Notes:"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        layout.addWidget(self.notes_edit)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Add initial row
        self._add_item_row()
    
    def _load_clients(self):
        """Load clients into combo"""
        with self.db.session() as session:
            clients = session.query(Client).order_by(Client.name).all()
            for client in clients:
                self.client_combo.addItem(client.name, client.id)
    
    def _load_invoice(self):
        """Load invoice data"""
        self.invoice_number.setText(self.invoice.invoice_number)
        
        # Find client in combo
        index = self.client_combo.findData(self.invoice.client_id)
        if index >= 0:
            self.client_combo.setCurrentIndex(index)
        
        if self.invoice.date:
            self.date_edit.setDate(QDate(self.invoice.date.year, self.invoice.date.month, self.invoice.date.day))
        
        if self.invoice.due_date:
            self.due_date_edit.setDate(QDate(self.invoice.due_date.year, self.invoice.due_date.month, self.invoice.due_date.day))
        
        status_index = self.status_combo.findText(self.invoice.status.title())
        if status_index >= 0:
            self.status_combo.setCurrentIndex(status_index)
        
        self.tax_rate.setValue(self.invoice.tax_rate or 0)
        self.notes_edit.setText(self.invoice.notes or "")
        
        # Load items
        self.items_table.setRowCount(0)
        try:
            items = json.loads(self.invoice.items or "[]")
            for item in items:
                self._add_item_row(item)
        except:
            self._add_item_row()
        
        self._calculate_totals()
    
    def _add_item_row(self, data: dict = None):
        """Add item row"""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        # Description
        desc = QLineEdit()
        desc.setPlaceholderText("Item description")
        desc.setStyleSheet("background: transparent; border: none; color: #e5e7eb; padding: 8px;")
        if data:
            desc.setText(data.get("description", ""))
        self.items_table.setCellWidget(row, 0, desc)
        
        # Quantity
        qty = QSpinBox()
        qty.setRange(1, 9999)
        qty.setValue(data.get("qty", 1) if data else 1)
        qty.setStyleSheet("background: transparent; border: none; color: #e5e7eb;")
        qty.valueChanged.connect(self._calculate_totals)
        self.items_table.setCellWidget(row, 1, qty)
        
        # Rate
        rate = QDoubleSpinBox()
        rate.setRange(0, 999999)
        rate.setPrefix("$")
        rate.setValue(data.get("rate", 0) if data else 0)
        rate.setStyleSheet("background: transparent; border: none; color: #e5e7eb;")
        rate.valueChanged.connect(self._calculate_totals)
        self.items_table.setCellWidget(row, 2, rate)
        
        # Amount (read-only)
        amount = QLabel("$0.00")
        amount.setStyleSheet("color: #10b981; font-weight: bold; padding: 8px;")
        self.items_table.setCellWidget(row, 3, amount)
        
        self._calculate_totals()
    
    def _remove_item_row(self):
        """Remove selected item row"""
        row = self.items_table.currentRow()
        if row >= 0:
            self.items_table.removeRow(row)
            self._calculate_totals()
    
    def _calculate_totals(self):
        """Calculate invoice totals"""
        subtotal = 0
        
        for row in range(self.items_table.rowCount()):
            qty_widget = self.items_table.cellWidget(row, 1)
            rate_widget = self.items_table.cellWidget(row, 2)
            amount_widget = self.items_table.cellWidget(row, 3)
            
            if qty_widget and rate_widget and amount_widget:
                qty = qty_widget.value()
                rate = rate_widget.value()
                amount = qty * rate
                subtotal += amount
                amount_widget.setText(f"${amount:.2f}")
        
        tax = subtotal * (self.tax_rate.value() / 100)
        total = subtotal + tax
        
        self.total_label.setText(f"Total: ${total:,.2f}")
    
    def _validate_and_accept(self):
        """Validate and accept"""
        if not self.invoice_number.text().strip():
            QMessageBox.warning(self, "Error", "Invoice number is required")
            return
        self.accept()
    
    def get_data(self) -> dict:
        """Get form data"""
        items = []
        subtotal = 0
        
        for row in range(self.items_table.rowCount()):
            desc_widget = self.items_table.cellWidget(row, 0)
            qty_widget = self.items_table.cellWidget(row, 1)
            rate_widget = self.items_table.cellWidget(row, 2)
            
            if desc_widget and qty_widget and rate_widget:
                desc = desc_widget.text().strip()
                if desc:
                    qty = qty_widget.value()
                    rate = rate_widget.value()
                    items.append({
                        "description": desc,
                        "qty": qty,
                        "rate": rate
                    })
                    subtotal += qty * rate
        
        tax_rate = self.tax_rate.value()
        total = subtotal * (1 + tax_rate / 100)
        
        date = self.date_edit.date()
        due_date = self.due_date_edit.date()
        
        return {
            "invoice_number": self.invoice_number.text().strip(),
            "client_id": self.client_combo.currentData(),
            "date": datetime(date.year(), date.month(), date.day()),
            "due_date": datetime(due_date.year(), due_date.month(), due_date.day()),
            "items": json.dumps(items),
            "subtotal": subtotal,
            "tax_rate": tax_rate,
            "total": total,
            "status": self.status_combo.currentText().lower(),
            "notes": self.notes_edit.toPlainText().strip() or None,
        }


class ExpenseDialog(QDialog):
    """Dialog for adding expenses"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Add Expense")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: #1f2937;
            }
            QLabel {
                color: #e5e7eb;
            }
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QDoubleSpinBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 8px;
                color: #e5e7eb;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        form = QFormLayout()
        
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Expense description*")
        form.addRow("Description:", self.desc_edit)
        
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999)
        self.amount_spin.setPrefix("$")
        form.addRow("Amount:", self.amount_spin)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(FinanceModule.EXPENSE_CATEGORIES)
        form.addRow("Category:", self.category_combo)
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form.addRow("Date:", self.date_edit)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        form.addRow("Notes:", self.notes_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _validate_and_accept(self):
        """Validate and accept"""
        if not self.desc_edit.text().strip():
            QMessageBox.warning(self, "Error", "Description is required")
            return
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Error", "Amount must be greater than 0")
            return
        self.accept()
    
    def get_data(self) -> dict:
        """Get form data"""
        date = self.date_edit.date()
        return {
            "description": self.desc_edit.text().strip(),
            "amount": self.amount_spin.value(),
            "category": self.category_combo.currentText(),
            "date": datetime(date.year(), date.month(), date.day()),
            "notes": self.notes_edit.toPlainText().strip() or None,
        }

"""
Lorem Ipsum Generator Module - Generate placeholder text
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QPlainTextEdit,
    QComboBox, QSpinBox, QCheckBox, QApplication,
    QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt
import random


class LoremGeneratorModule(QWidget):
    """Lorem Ipsum Generator Module"""
    
    # Lorem ipsum words
    LOREM_WORDS = [
        "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit",
        "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore", "et", "dolore",
        "magna", "aliqua", "enim", "ad", "minim", "veniam", "quis", "nostrud",
        "exercitation", "ullamco", "laboris", "nisi", "aliquip", "ex", "ea", "commodo",
        "consequat", "duis", "aute", "irure", "in", "reprehenderit", "voluptate",
        "velit", "esse", "cillum", "fugiat", "nulla", "pariatur", "excepteur", "sint",
        "occaecat", "cupidatat", "non", "proident", "sunt", "culpa", "qui", "officia",
        "deserunt", "mollit", "anim", "id", "est", "laborum", "ac", "ante", "bibendum",
        "blandit", "condimentum", "congue", "cras", "cum", "curabitur", "cursus",
        "dapibus", "dictum", "dignissim", "dis", "donec", "dui", "egestas", "eleifend",
        "elementum", "etiam", "eu", "euismod", "facilisi", "facilisis", "fames",
        "faucibus", "felis", "fermentum", "feugiat", "fringilla", "gravida", "habitant",
        "habitasse", "hac", "hendrerit", "himenaeos", "iaculis", "imperdiet", "integer",
        "interdum", "justo", "lacinia", "lacus", "laoreet", "lectus", "leo", "libero",
        "ligula", "litora", "lobortis", "luctus", "maecenas", "massa", "mattis",
        "mauris", "metus", "mi", "montes", "morbi", "nam", "nascetur", "natoque",
        "nec", "neque", "nibh", "nunc", "odio", "orci", "ornare", "pellentesque",
        "penatibus", "per", "pharetra", "phasellus", "placerat", "platea", "porta",
        "porttitor", "posuere", "potenti", "praesent", "pretium", "primis", "proin",
        "pulvinar", "purus", "quam", "quisque", "rhoncus", "ridiculus", "risus",
        "rutrum", "sagittis", "sapien", "scelerisque", "semper", "senectus", "sociosqu",
        "sodales", "sollicitudin", "suscipit", "suspendisse", "taciti", "tellus",
        "tempus", "tincidunt", "torquent", "tortor", "tristique", "turpis", "ultrices",
        "ultricies", "urna", "varius", "vehicula", "vel", "venenatis", "vestibulum",
        "vitae", "vivamus", "viverra", "volutpat", "vulputate"
    ]
    
    # First names
    FIRST_NAMES = [
        "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
        "Thomas", "Charles", "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth",
        "Barbara", "Susan", "Jessica", "Sarah", "Karen", "Emma", "Olivia", "Ava",
        "Isabella", "Sophia", "Mia", "Charlotte", "Amelia", "Harper", "Evelyn"
    ]
    
    # Last names
    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
        "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
    ]
    
    # Email domains
    EMAIL_DOMAINS = [
        "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com",
        "example.com", "test.com", "company.com", "email.com", "mail.com"
    ]
    
    # Company suffixes
    COMPANY_SUFFIXES = [
        "Inc", "LLC", "Corp", "Ltd", "Group", "Solutions", "Technologies", "Systems",
        "Industries", "Services", "Enterprises", "Holdings", "Partners", "Associates"
    ]
    
    # Street types
    STREET_TYPES = [
        "Street", "Avenue", "Boulevard", "Road", "Lane", "Drive", "Court", "Way",
        "Place", "Circle", "Trail", "Parkway", "Highway", "Square"
    ]
    
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
        title = QLabel("📝 Lorem Ipsum Generator")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f9fafb;
            }
        """)
        layout.addWidget(title)
        
        # Main content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)
        
        # Left - Options
        self.options_frame = QFrame(self)
        self.options_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        self.options_frame.setFixedWidth(300)
        options_layout = QVBoxLayout(self.options_frame)
        options_layout.setContentsMargins(20, 20, 20, 20)
        options_layout.setSpacing(16)
        
        # Generator type
        type_label = QLabel("Generator Type")
        type_label.setStyleSheet("color: #f9fafb; font-weight: bold;")
        options_layout.addWidget(type_label)
        
        self.type_group = QButtonGroup()
        
        types = [
            ("Lorem Ipsum", "lorem"),
            ("Random Names", "names"),
            ("Email Addresses", "emails"),
            ("Phone Numbers", "phones"),
            ("Addresses", "addresses"),
            ("Company Names", "companies"),
            ("Numbers", "numbers"),
            ("Dates", "dates"),
        ]
        
        for label, value in types:
            radio = QRadioButton(label)
            radio.setStyleSheet("color: #e5e7eb;")
            radio.setProperty("value", value)
            self.type_group.addButton(radio)
            options_layout.addWidget(radio)
            if value == "lorem":
                radio.setChecked(True)
        
        self.type_group.buttonClicked.connect(self._on_type_changed)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #374151;")
        options_layout.addWidget(sep)
        
        # Options section
        options_label = QLabel("Options")
        options_label.setStyleSheet("color: #f9fafb; font-weight: bold;")
        options_layout.addWidget(options_label)
        
        # Count
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Count:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 1000)
        self.count_spin.setValue(5)
        self.count_spin.setStyleSheet("""
            QSpinBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px;
                color: #e5e7eb;
            }
        """)
        count_layout.addWidget(self.count_spin)
        count_layout.addStretch()
        options_layout.addLayout(count_layout)
        
        # Unit type (for lorem)
        unit_layout = QHBoxLayout()
        unit_layout.addWidget(QLabel("Unit:"))
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Paragraphs", "Sentences", "Words"])
        self.unit_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px 12px;
                color: #e5e7eb;
            }
        """)
        unit_layout.addWidget(self.unit_combo)
        unit_layout.addStretch()
        options_layout.addLayout(unit_layout)
        
        # Additional options
        self.start_lorem_check = QCheckBox("Start with \"Lorem ipsum...\"")
        self.start_lorem_check.setChecked(True)
        self.start_lorem_check.setStyleSheet("color: #9ca3af;")
        options_layout.addWidget(self.start_lorem_check)
        
        self.html_tags_check = QCheckBox("Add HTML <p> tags")
        self.html_tags_check.setStyleSheet("color: #9ca3af;")
        options_layout.addWidget(self.html_tags_check)
        
        options_layout.addStretch()
        
        # Generate button
        generate_btn = QPushButton("🔄 Generate")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                border: none;
                border-radius: 8px;
                padding: 14px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #818cf8;
            }
        """)
        generate_btn.clicked.connect(self._generate)
        options_layout.addWidget(generate_btn)
        
        content_layout.addWidget(self.options_frame)
        
        # Right - Output
        self.output_frame = QFrame(self)
        self.output_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
            }
        """)
        output_layout = QVBoxLayout(self.output_frame)
        output_layout.setContentsMargins(20, 20, 20, 20)
        output_layout.setSpacing(12)
        
        # Header
        output_header = QHBoxLayout()
        output_label = QLabel("Generated Text")
        output_label.setStyleSheet("color: #f9fafb; font-weight: bold;")
        output_header.addWidget(output_label)
        output_header.addStretch()
        
        # Stats
        self.stats_label = QLabel("0 chars, 0 words")
        self.stats_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        output_header.addWidget(self.stats_label)
        
        copy_btn = QPushButton("📋 Copy")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        copy_btn.clicked.connect(self._copy_output)
        output_header.addWidget(copy_btn)
        
        output_layout.addLayout(output_header)
        
        # Output text area
        self.output_edit = QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 16px;
                color: #e5e7eb;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        output_layout.addWidget(self.output_edit)
        
        content_layout.addWidget(self.output_frame, 1)
        
        layout.addLayout(content_layout, 1)
        
        # Quick presets
        self.presets_frame = QFrame(self)
        self.presets_frame.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 8px;
                border: 1px solid #374151;
            }
        """)
        presets_layout = QHBoxLayout(self.presets_frame)
        presets_layout.setContentsMargins(16, 12, 16, 12)
        
        presets_label = QLabel("Quick Presets:")
        presets_label.setStyleSheet("color: #9ca3af;")
        presets_layout.addWidget(presets_label)
        
        presets = [
            ("1 Paragraph", ("lorem", 1, "Paragraphs")),
            ("3 Paragraphs", ("lorem", 3, "Paragraphs")),
            ("5 Sentences", ("lorem", 5, "Sentences")),
            ("100 Words", ("lorem", 100, "Words")),
            ("10 Names", ("names", 10, None)),
            ("10 Emails", ("emails", 10, None)),
        ]
        
        for label, preset in presets:
            btn = QPushButton(label)
            btn.setStyleSheet("""
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
            btn.clicked.connect(lambda checked, p=preset: self._apply_preset(p))
            presets_layout.addWidget(btn)
        
        presets_layout.addStretch()
        layout.addWidget(self.presets_frame)
        
        # Generate initial content
        self._generate()
    
    def _on_type_changed(self, button):
        """Handle type change"""
        gen_type = button.property("value")
        is_lorem = gen_type == "lorem"
        self.unit_combo.setEnabled(is_lorem)
        self.start_lorem_check.setEnabled(is_lorem)
        self.html_tags_check.setEnabled(is_lorem)
    
    def _generate(self):
        """Generate content based on selected type"""
        checked_btn = self.type_group.checkedButton()
        if not checked_btn:
            return
        
        gen_type = checked_btn.property("value")
        count = self.count_spin.value()
        
        if gen_type == "lorem":
            result = self._generate_lorem(count)
        elif gen_type == "names":
            result = self._generate_names(count)
        elif gen_type == "emails":
            result = self._generate_emails(count)
        elif gen_type == "phones":
            result = self._generate_phones(count)
        elif gen_type == "addresses":
            result = self._generate_addresses(count)
        elif gen_type == "companies":
            result = self._generate_companies(count)
        elif gen_type == "numbers":
            result = self._generate_numbers(count)
        elif gen_type == "dates":
            result = self._generate_dates(count)
        else:
            result = ""
        
        self.output_edit.setPlainText(result)
        
        # Update stats
        chars = len(result)
        words = len(result.split())
        self.stats_label.setText(f"{chars:,} chars, {words:,} words")
    
    def _generate_lorem(self, count: int) -> str:
        """Generate lorem ipsum text"""
        unit = self.unit_combo.currentText()
        start_lorem = self.start_lorem_check.isChecked()
        html_tags = self.html_tags_check.isChecked()
        
        if unit == "Words":
            words = self._generate_words(count, start_lorem)
            return " ".join(words)
        
        elif unit == "Sentences":
            sentences = []
            for i in range(count):
                word_count = random.randint(8, 20)
                use_start = start_lorem and i == 0
                words = self._generate_words(word_count, use_start)
                sentence = " ".join(words).capitalize() + "."
                sentences.append(sentence)
            return " ".join(sentences)
        
        else:  # Paragraphs
            paragraphs = []
            for i in range(count):
                sentence_count = random.randint(4, 8)
                sentences = []
                for j in range(sentence_count):
                    word_count = random.randint(8, 20)
                    use_start = start_lorem and i == 0 and j == 0
                    words = self._generate_words(word_count, use_start)
                    sentence = " ".join(words).capitalize() + "."
                    sentences.append(sentence)
                para = " ".join(sentences)
                if html_tags:
                    para = f"<p>{para}</p>"
                paragraphs.append(para)
            return "\n\n".join(paragraphs)
    
    def _generate_words(self, count: int, start_lorem: bool = False) -> list:
        """Generate random lorem words"""
        if start_lorem and count >= 2:
            words = ["lorem", "ipsum"]
            words.extend(random.choices(self.LOREM_WORDS, k=count - 2))
        else:
            words = random.choices(self.LOREM_WORDS, k=count)
        return words
    
    def _generate_names(self, count: int) -> str:
        """Generate random names"""
        names = []
        for _ in range(count):
            first = random.choice(self.FIRST_NAMES)
            last = random.choice(self.LAST_NAMES)
            names.append(f"{first} {last}")
        return "\n".join(names)
    
    def _generate_emails(self, count: int) -> str:
        """Generate random email addresses"""
        emails = []
        for _ in range(count):
            first = random.choice(self.FIRST_NAMES).lower()
            last = random.choice(self.LAST_NAMES).lower()
            domain = random.choice(self.EMAIL_DOMAINS)
            separator = random.choice([".", "_", ""])
            email = f"{first}{separator}{last}@{domain}"
            emails.append(email)
        return "\n".join(emails)
    
    def _generate_phones(self, count: int) -> str:
        """Generate random phone numbers"""
        phones = []
        for _ in range(count):
            area = random.randint(200, 999)
            prefix = random.randint(200, 999)
            line = random.randint(1000, 9999)
            fmt = random.choice([
                f"({area}) {prefix}-{line}",
                f"{area}-{prefix}-{line}",
                f"+1 {area} {prefix} {line}",
            ])
            phones.append(fmt)
        return "\n".join(phones)
    
    def _generate_addresses(self, count: int) -> str:
        """Generate random addresses"""
        addresses = []
        for _ in range(count):
            number = random.randint(100, 9999)
            street_name = random.choice(self.LAST_NAMES)
            street_type = random.choice(self.STREET_TYPES)
            city = random.choice(self.LAST_NAMES) + random.choice(["ville", "ton", "burg", " City", " Town"])
            state = random.choice(["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"])
            zipcode = random.randint(10000, 99999)
            
            address = f"{number} {street_name} {street_type}\n{city}, {state} {zipcode}"
            addresses.append(address)
        return "\n\n".join(addresses)
    
    def _generate_companies(self, count: int) -> str:
        """Generate random company names"""
        companies = []
        prefixes = ["Tech", "Global", "Prime", "Smart", "Next", "First", "Pro", "Elite", "Dynamic", "United"]
        words = ["Data", "Digital", "Cloud", "Web", "Net", "Soft", "Info", "Logic", "Core", "Base"]
        
        for _ in range(count):
            style = random.randint(1, 4)
            if style == 1:
                name = f"{random.choice(prefixes)}{random.choice(words)} {random.choice(self.COMPANY_SUFFIXES)}"
            elif style == 2:
                name = f"{random.choice(self.LAST_NAMES)} & {random.choice(self.LAST_NAMES)} {random.choice(self.COMPANY_SUFFIXES)}"
            elif style == 3:
                name = f"{random.choice(self.LAST_NAMES)} {random.choice(words)} {random.choice(self.COMPANY_SUFFIXES)}"
            else:
                name = f"{random.choice(prefixes)} {random.choice(self.LAST_NAMES)} {random.choice(self.COMPANY_SUFFIXES)}"
            companies.append(name)
        return "\n".join(companies)
    
    def _generate_numbers(self, count: int) -> str:
        """Generate random numbers"""
        numbers = [str(random.randint(1, 1000000)) for _ in range(count)]
        return "\n".join(numbers)
    
    def _generate_dates(self, count: int) -> str:
        """Generate random dates"""
        import datetime
        dates = []
        for _ in range(count):
            year = random.randint(2020, 2025)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            d = datetime.date(year, month, day)
            fmt = random.choice([
                d.strftime("%Y-%m-%d"),
                d.strftime("%m/%d/%Y"),
                d.strftime("%B %d, %Y"),
            ])
            dates.append(fmt)
        return "\n".join(dates)
    
    def _apply_preset(self, preset: tuple):
        """Apply a preset configuration"""
        gen_type, count, unit = preset
        
        # Find and select the right radio button
        for btn in self.type_group.buttons():
            if btn.property("value") == gen_type:
                btn.setChecked(True)
                break
        
        self.count_spin.setValue(count)
        
        if unit:
            self.unit_combo.setCurrentText(unit)
        
        self._generate()
    
    def _copy_output(self):
        """Copy output to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.output_edit.toPlainText())

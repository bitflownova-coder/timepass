"""
Bitflow Developer Toolkit - Desktop Application
A comprehensive developer productivity suite
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtGui import QIcon, QFont

# Note: High DPI scaling is enabled by default in PyQt6

def main():
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Bitflow Developer Toolkit")
    app.setOrganizationName("Bitflow Software")
    app.setOrganizationDomain("bitflow.dev")
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Apply modern styling
    try:
        from qt_material import apply_stylesheet
        apply_stylesheet(app, theme='dark_teal.xml')
    except ImportError:
        # Fallback to basic dark theme
        app.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                color: white;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
            QListWidget, QTreeWidget, QTableWidget {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
        """)
    
    # Import and create main window
    from core.main_window import MainWindow
    
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

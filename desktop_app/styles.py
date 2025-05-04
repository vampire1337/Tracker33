from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

def setup_dark_theme(app):
    # Устанавливаем темную тему
    app.setStyle("Fusion")
    
    # Создаем палитру
    palette = QPalette()
    
    # Устанавливаем цвета для различных элементов
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    
    app.setPalette(palette)

# Стили для различных элементов
STYLES = {
    "QMainWindow": """
        QMainWindow {
            background-color: #353535;
        }
    """,
    "QPushButton": """
        QPushButton {
            background-color: #2a82da;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1f6cb3;
        }
        QPushButton:pressed {
            background-color: #1a5a96;
        }
        QPushButton:disabled {
            background-color: #666666;
        }
    """,
    "QLineEdit": """
        QLineEdit {
            background-color: #191919;
            color: white;
            border: 1px solid #2a82da;
            border-radius: 4px;
            padding: 8px;
        }
        QLineEdit:focus {
            border: 2px solid #2a82da;
        }
    """,
    "QListWidget": """
        QListWidget {
            background-color: #191919;
            color: white;
            border: 1px solid #2a82da;
            border-radius: 4px;
        }
        QListWidget::item {
            padding: 8px;
            border-bottom: 1px solid #353535;
        }
        QListWidget::item:selected {
            background-color: #2a82da;
        }
    """,
    "QLabel": """
        QLabel {
            color: white;
            font-size: 14px;
        }
    """,
    "QMessageBox": """
        QMessageBox {
            background-color: #353535;
        }
        QMessageBox QLabel {
            color: white;
        }
        QMessageBox QPushButton {
            background-color: #2a82da;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
    """
} 
"""
Process Button Widget - Button for active processes in sidebar
"""
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from styles.futuristic_theme import get_theme


class ProcessButton(QPushButton):
    """Custom process button widget for sidebar"""

    # Signal emitted when button is clicked
    clicked = pyqtSignal(int)  # process_id

    def __init__(self, process_id: int, process_name: str, step_count: int = 0, parent=None):
        super().__init__(parent)
        self.process_id = process_id
        self.process_name = process_name
        self.step_count = step_count
        self.is_active = False
        self.theme = get_theme()

        self.init_ui()

    def init_ui(self):
        """Initialize button UI"""
        # Set button text with step count if available
        if self.step_count > 0:
            button_text = f"{self.process_name}\n({self.step_count})"
        else:
            button_text = self.process_name

        self.setText(button_text)

        # Set tooltip with full process name and step count
        tooltip = f"Proceso: {self.process_name}"
        if self.step_count > 0:
            tooltip += f"\n{self.step_count} paso{'s' if self.step_count != 1 else ''}"
        self.setToolTip(tooltip)

        # Set fixed size - same width as category buttons
        self.setFixedSize(70, 60)

        # Set font
        font = QFont()
        font.setPointSize(9)
        font.setBold(False)
        self.setFont(font)

        # Enable cursor change on hover
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Apply default style
        self.update_style()

    def update_style(self):
        """Update button style based on state"""
        if self.is_active:
            # Active state - with accent border and gradient background
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #1a3d4d;
                    color: {self.theme.get_color('text_primary')};
                    border: 2px solid {self.theme.get_color('primary')};
                    border-left: 5px solid {self.theme.get_color('primary')};
                    border-radius: 4px;
                    padding: 5px;
                    text-align: center;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.theme.get_color('primary')},
                        stop:1 {self.theme.get_color('secondary')}
                    );
                    border: 2px solid {self.theme.get_color('primary')};
                    border-left: 5px solid {self.theme.get_color('primary')};
                }}
            """)
        else:
            # Normal state
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #2d2d2d;
                    color: {self.theme.get_color('text_secondary')};
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    padding: 5px;
                    text-align: center;
                }}
                QPushButton:hover {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.theme.get_color('primary')},
                        stop:1 {self.theme.get_color('secondary')}
                    );
                    color: {self.theme.get_color('text_primary')};
                    border: 2px solid {self.theme.get_color('primary')};
                }}
                QPushButton:pressed {{
                    background-color: #1d1d1d;
                }}
            """)

    def set_active(self, active: bool):
        """Set button active state"""
        self.is_active = active
        self.update_style()

    def mousePressEvent(self, event):
        """Handle mouse press - emit signal with process_id"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.process_id)
        super().mousePressEvent(event)

    def sizeHint(self) -> QSize:
        """Recommended size"""
        return QSize(70, 60)

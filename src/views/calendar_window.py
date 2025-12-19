"""
Calendar Window
Main window for calendar events and alerts management
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import logging

from .calendar.events_list import EventsList
from .alerts.alerts_list import AlertsList
from .dialogs.event_editor_dialog import EventEditorDialog
from .dialogs.alert_editor_dialog import AlertEditorDialog
from .dialogs.notification_dialog import NotificationDialog
from src.core.alert_service import AlertService

logger = logging.getLogger(__name__)


class CalendarWindow(QMainWindow):
    """
    Calendar window with events and alerts management
    Simple tabbed interface for viewing and managing calendar items
    """

    # Signal emitted when window is closed
    window_closed = pyqtSignal()

    def __init__(self, controller, parent=None):
        """
        Initialize calendar window

        Args:
            controller: MainController instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.controller = controller
        self.db = controller.config_manager.db if controller else None

        self.setup_window()
        self.setup_ui()
        self.apply_styles()

        # Initialize and start AlertService
        self.setup_alert_service()

        # Position window centered on screen
        self.center_on_screen()

        logger.info("CalendarWindow initialized")

    def setup_window(self):
        """Configure window properties"""
        self.setWindowTitle("Calendario - SidePanel")
        self.setMinimumSize(900, 600)

        # Set window flags: Frameless and stay on top
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        # Set window attribute to show on taskbar
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)

    def setup_ui(self):
        """Setup the user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add custom title bar
        main_layout.addWidget(self.create_title_bar())

        # Add tab widget
        self.tab_widget = QTabWidget()

        # Events tab with EventsList
        self.events_list = EventsList(self.db)
        # Connect signals (editors will be implemented in Phase 7)
        self.events_list.create_event_requested.connect(self.on_create_event_requested)
        self.events_list.edit_event_requested.connect(self.on_edit_event_requested)

        # Alerts tab with AlertsList
        self.alerts_list = AlertsList(self.db)
        # Connect signals (editors will be implemented in Phase 7)
        self.alerts_list.create_alert_requested.connect(self.on_create_alert_requested)
        self.alerts_list.edit_alert_requested.connect(self.on_edit_alert_requested)

        self.tab_widget.addTab(self.events_list, "📅 Eventos")
        self.tab_widget.addTab(self.alerts_list, "🔔 Alertas")

        main_layout.addWidget(self.tab_widget)

    def create_title_bar(self):
        """
        Create custom title bar with window controls

        Returns:
            QWidget: Title bar widget
        """
        title_bar = QWidget()
        title_bar.setFixedHeight(45)
        title_bar.setObjectName("titleBar")

        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(15, 0, 5, 0)
        layout.setSpacing(10)

        # Window icon and title
        title_label = QLabel("📅 Calendario y Alertas")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)

        layout.addWidget(title_label)
        layout.addStretch()

        # Window control buttons
        btn_minimize = QPushButton("−")
        btn_minimize.setObjectName("titleBarButton")
        btn_minimize.setFixedSize(40, 30)
        btn_minimize.setToolTip("Minimizar")
        btn_minimize.clicked.connect(self.showMinimized)

        btn_maximize = QPushButton("□")
        btn_maximize.setObjectName("titleBarButton")
        btn_maximize.setFixedSize(40, 30)
        btn_maximize.setToolTip("Maximizar/Restaurar")
        btn_maximize.clicked.connect(self.toggle_maximize)
        self.btn_maximize = btn_maximize  # Store reference to update icon

        btn_close = QPushButton("×")
        btn_close.setObjectName("titleBarButtonClose")
        btn_close.setFixedSize(40, 30)
        btn_close.setToolTip("Cerrar")
        btn_close.clicked.connect(self.close)

        layout.addWidget(btn_minimize)
        layout.addWidget(btn_maximize)
        layout.addWidget(btn_close)

        # Enable dragging window by title bar
        title_bar.mousePressEvent = self.title_bar_mouse_press
        title_bar.mouseMoveEvent = self.title_bar_mouse_move

        return title_bar

    def toggle_maximize(self):
        """Toggle between maximized and normal window state"""
        if self.isMaximized():
            self.showNormal()
            self.btn_maximize.setText("□")
        else:
            self.showMaximized()
            self.btn_maximize.setText("❐")

    def title_bar_mouse_press(self, event):
        """Handle mouse press on title bar for window dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def title_bar_mouse_move(self, event):
        """Handle mouse move on title bar for window dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            # Only allow dragging when not maximized
            if self.isMaximized():
                return
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def center_on_screen(self):
        """Center the window on the screen with appropriate size"""
        from PyQt6.QtGui import QGuiApplication

        # Get the primary screen
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        # Set window size to 80% of screen size
        window_width = int(screen_geometry.width() * 0.8)
        window_height = int(screen_geometry.height() * 0.8)
        self.resize(window_width, window_height)

        # Center the window on screen
        x = screen_geometry.left() + (screen_geometry.width() - window_width) // 2
        y = screen_geometry.top() + (screen_geometry.height() - window_height) // 2
        self.move(x, y)

        logger.debug(f"Window centered at ({x}, {y}) with size ({window_width}x{window_height})")

    def apply_styles(self):
        """Apply dark theme styles to the window"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #cccccc;
            }

            /* Custom Title Bar */
            #titleBar {
                background-color: #1e1e1e;
                border-bottom: 1px solid #3d3d3d;
            }

            #titleBarButton {
                background-color: transparent;
                color: #cccccc;
                border: none;
                border-radius: 3px;
                font-size: 16pt;
                font-weight: bold;
            }

            #titleBarButton:hover {
                background-color: #3d3d3d;
            }

            #titleBarButtonClose {
                background-color: transparent;
                color: #cccccc;
                border: none;
                border-radius: 3px;
                font-size: 18pt;
                font-weight: bold;
            }

            #titleBarButtonClose:hover {
                background-color: #e81123;
                color: #ffffff;
            }

            /* Tab Widget */
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                background-color: #2b2b2b;
                margin-top: -1px;
            }

            QTabBar::tab {
                background-color: #252525;
                color: #cccccc;
                padding: 12px 24px;
                margin-right: 2px;
                border: 1px solid #3d3d3d;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 10pt;
            }

            QTabBar::tab:selected {
                background-color: #2b2b2b;
                color: #ffffff;
                border-bottom: 2px solid #007acc;
            }

            QTabBar::tab:hover:!selected {
                background-color: #2d2d2d;
            }

            /* Labels */
            QLabel {
                color: #cccccc;
                padding: 20px;
                font-size: 11pt;
            }
        """)

    def on_create_event_requested(self):
        """Handle create event request - open EventEditorDialog"""
        logger.info("Create event requested")
        dialog = EventEditorDialog(self.db, parent=self)
        if dialog.exec():
            # Refresh events list after creation
            self.refresh_events()
            logger.debug("Event created, list refreshed")

    def on_edit_event_requested(self, event):
        """
        Handle edit event request - open EventEditorDialog

        Args:
            event: Event dictionary to edit
        """
        logger.info(f"Edit event requested: {event['id']}")
        dialog = EventEditorDialog(self.db, event=event, parent=self)
        if dialog.exec():
            # Refresh events list after edit
            self.refresh_events()
            logger.debug("Event edited, list refreshed")

    def on_create_alert_requested(self):
        """Handle create alert request - open AlertEditorDialog"""
        logger.info("Create alert requested")
        dialog = AlertEditorDialog(self.db, parent=self)
        if dialog.exec():
            # Refresh alerts list after creation
            self.refresh_alerts()
            logger.debug("Alert created, list refreshed")

    def on_edit_alert_requested(self, alert):
        """
        Handle edit alert request - open AlertEditorDialog

        Args:
            alert: Alert dictionary to edit
        """
        logger.info(f"Edit alert requested: {alert['id']}")
        dialog = AlertEditorDialog(self.db, alert=alert, parent=self)
        if dialog.exec():
            # Refresh alerts list after edit
            self.refresh_alerts()
            logger.debug("Alert edited, list refreshed")

    def setup_alert_service(self):
        """Initialize and start the AlertService"""
        if self.db:
            try:
                # Create AlertService with 60-second check interval
                self.alert_service = AlertService(self.db, check_interval=60000)

                # Connect alert_triggered signal to show notification
                self.alert_service.alert_triggered.connect(self.on_alert_triggered)

                # Start the service
                self.alert_service.start()

                logger.info("AlertService initialized and started in CalendarWindow")
            except Exception as e:
                logger.error(f"Error initializing AlertService: {e}", exc_info=True)
        else:
            logger.warning("AlertService not initialized: no database connection")

    def on_alert_triggered(self, alert, item):
        """
        Handle alert triggered by AlertService
        Shows notification dialog

        Args:
            alert: Alert dictionary
            item: Item dictionary
        """
        logger.info(f"Alert triggered: {alert.get('id')} - {alert.get('alert_title')}")

        try:
            # Show notification dialog
            notification = NotificationDialog(alert, item, self)
            notification.exec()

            # Refresh alerts list to show updated status
            self.refresh_alerts()

            logger.debug("Notification shown and alerts refreshed")

        except Exception as e:
            logger.error(f"Error showing notification: {e}", exc_info=True)

    def refresh_events(self):
        """Refresh the events list"""
        if hasattr(self, 'events_list'):
            self.events_list.load_events()
            logger.debug("Events list refreshed")

    def refresh_alerts(self):
        """Refresh the alerts list"""
        if hasattr(self, 'alerts_list'):
            self.alerts_list.load_alerts()
            logger.debug("Alerts list refreshed")

    def closeEvent(self, event):
        """Handle window close event"""
        # Stop AlertService
        if hasattr(self, 'alert_service'):
            self.alert_service.stop()
            logger.info("AlertService stopped")

        logger.info("CalendarWindow closed")
        self.window_closed.emit()
        event.accept()

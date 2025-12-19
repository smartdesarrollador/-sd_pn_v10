"""
Related Items Floating Panel - Displays items related to tags, categories, or lists
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QScrollArea, QPushButton, QCheckBox, QSizePolicy,
                             QGraphicsDropShadowEffect, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QCursor, QColor
import sys
import logging
from pathlib import Path
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.models.item import Item
from src.views.widgets.related_item_card import RelatedItemCard
from styles.futuristic_theme import get_theme
from styles.panel_styles import PanelStyles
from src.utils.panel_resizer import PanelResizer

# Get logger
logger = logging.getLogger(__name__)


class RelationType(Enum):
    """Tipos de relación para items"""
    TAG = "tag"
    CATEGORY = "category"
    LIST = "list"
    PROJECT = "project"


class RelatedItemsFloatingPanel(QWidget):
    """Panel flotante para mostrar items relacionados a tags, categorías o listas"""

    # Señales
    item_copied = pyqtSignal(object)  # Item object
    item_selected = pyqtSignal(object)  # Item object
    item_edit_requested = pyqtSignal(object)  # Item object a editar
    selection_changed = pyqtSignal(list)  # Lista de items seleccionados
    items_deleted = pyqtSignal(list)  # Lista de IDs de items eliminados
    items_favorited = pyqtSignal(list, bool)  # Lista de IDs de items, is_favorite
    panel_closed = pyqtSignal()

    def __init__(self, relation_type: RelationType, entity_id: int, entity_name: str,
                 entity_icon: str = "", items: list = None, db_manager=None, parent=None):
        super().__init__(parent)

        # Datos del panel
        self.relation_type = relation_type
        self.entity_id = entity_id
        self.entity_name = entity_name
        self.entity_icon = entity_icon
        self.items = items or []
        self.selected_items = []  # Items actualmente seleccionados
        self.db_manager = db_manager  # Para guardar/restaurar estado

        # UI state
        self.is_minimized = False
        self.is_maximized = False
        self.normal_geometry = None  # Para guardar geometría antes de maximizar

        # Display options (checkboxes state)
        self.show_labels = True
        self.show_tags = False
        self.show_content = False
        self.show_description = False

        # Theme
        self.theme = get_theme()

        # Panel resizer (se inicializa en init_ui)
        self.panel_resizer = None

        # Drag window variables
        self.drag_position = None

        # Timer para guardar estado (debounce)
        self.save_state_timer = QTimer()
        self.save_state_timer.setSingleShot(True)
        self.save_state_timer.timeout.connect(self._save_state_to_db)

        self.init_ui()
        self._setup_shadow_effect()  # Agregar sombra
        self._restore_state_from_db()  # Restaurar estado guardado
        self._animate_entrance()  # Animación de entrada

    def init_ui(self):
        """Inicializar la interfaz del panel flotante"""
        # Window properties - Hacer ventana COMPLETAMENTE independiente
        self.setWindowTitle(f"Items - {self.entity_name}")

        # Flags para ventana independiente que NO se minimiza con el padre
        self.setWindowFlags(
            Qt.WindowType.Window |  # Ventana independiente del sistema
            Qt.WindowType.WindowStaysOnTopHint |  # Siempre visible
            Qt.WindowType.FramelessWindowHint |  # Sin borde del sistema
            Qt.WindowType.WindowMinimizeButtonHint |  # Permitir minimización
            Qt.WindowType.WindowMaximizeButtonHint  # Permitir maximización
        )

        # Atributos para mantener ventana completamente independiente
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)  # No eliminar al cerrar
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)  # No cerrar app al cerrar este widget
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)  # Activar al mostrar

        # Set window size
        self.setMinimumWidth(PanelStyles.PANEL_WIDTH_MIN)
        self.setMaximumWidth(PanelStyles.PANEL_WIDTH_MAX)
        self.setMinimumHeight(PanelStyles.PANEL_HEIGHT_MIN)
        self.setMaximumHeight(PanelStyles.PANEL_HEIGHT_MAX)
        self.resize(500, 600)  # Tamaño inicial

        # Enable mouse tracking for resizer
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        # Set window opacity
        self.setWindowOpacity(0.98)

        # Apply enhanced panel styles
        self.setStyleSheet(self._get_enhanced_panel_style())

        # Initialize panel resizer
        self.panel_resizer = PanelResizer(
            widget=self,
            min_width=PanelStyles.PANEL_WIDTH_MIN,
            max_width=PanelStyles.PANEL_WIDTH_MAX,
            min_height=PanelStyles.PANEL_HEIGHT_MIN,
            max_height=PanelStyles.PANEL_HEIGHT_MAX,
            handle_size=PanelStyles.RESIZE_HANDLE_SIZE
        )

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ========== HEADER ==========
        self.header_widget = QWidget()
        self.header_widget.setStyleSheet(PanelStyles.get_header_style())
        self.header_widget.setFixedHeight(PanelStyles.HEADER_HEIGHT)
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(
            PanelStyles.HEADER_PADDING_H,
            PanelStyles.HEADER_PADDING_V,
            PanelStyles.HEADER_PADDING_H,
            PanelStyles.HEADER_PADDING_V
        )
        header_layout.setSpacing(6)

        # Title label
        title_text = f"{self.entity_icon} {self.entity_name}" if self.entity_icon else self.entity_name
        self.header_label = QLabel(title_text)
        self.header_label.setStyleSheet(PanelStyles.get_header_title_style())
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.header_label, 1)

        # Pin button (verde cuando está anclado)
        self.pin_button = QPushButton("📌")
        self.pin_button.setFixedSize(PanelStyles.CLOSE_BUTTON_SIZE, PanelStyles.CLOSE_BUTTON_SIZE)
        self.pin_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pin_button.setStyleSheet(PanelStyles.get_close_button_style())
        self.pin_button.setToolTip("Anclar panel")
        self.pin_button.clicked.connect(self.toggle_pin)
        header_layout.addWidget(self.pin_button)

        # Minimize button
        self.minimize_button = QPushButton("−")
        self.minimize_button.setFixedSize(PanelStyles.CLOSE_BUTTON_SIZE, PanelStyles.CLOSE_BUTTON_SIZE)
        self.minimize_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.minimize_button.setStyleSheet(PanelStyles.get_close_button_style())
        self.minimize_button.setToolTip("Minimizar panel")
        self.minimize_button.clicked.connect(self.toggle_minimize)
        header_layout.addWidget(self.minimize_button)

        # Maximize button
        self.maximize_button = QPushButton("□")
        self.maximize_button.setFixedSize(PanelStyles.CLOSE_BUTTON_SIZE, PanelStyles.CLOSE_BUTTON_SIZE)
        self.maximize_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.maximize_button.setStyleSheet(PanelStyles.get_close_button_style())
        self.maximize_button.setToolTip("Maximizar panel")
        self.maximize_button.clicked.connect(self.toggle_maximize)
        header_layout.addWidget(self.maximize_button)

        # Close button
        close_button = QPushButton("✕")
        close_button.setFixedSize(PanelStyles.CLOSE_BUTTON_SIZE, PanelStyles.CLOSE_BUTTON_SIZE)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.setStyleSheet(PanelStyles.get_close_button_style())
        close_button.setToolTip("Cerrar panel")
        close_button.clicked.connect(self.close)
        header_layout.addWidget(close_button)

        main_layout.addWidget(self.header_widget)

        # ========== DISPLAY OPTIONS ROW (Checkboxes) ==========
        self.display_options_widget = QWidget()
        self.display_options_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme.get_color('background_mid')};
                border-bottom: 1px solid {self.theme.get_color('surface')};
            }}
        """)
        display_options_layout = QHBoxLayout(self.display_options_widget)
        display_options_layout.setContentsMargins(15, 5, 15, 5)
        display_options_layout.setSpacing(15)

        # Label "Mostrar:"
        display_label = QLabel("Mostrar:")
        display_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_secondary')};
                font-size: 9pt;
                font-weight: bold;
            }}
        """)
        display_options_layout.addWidget(display_label)

        # Checkbox: Labels
        self.show_labels_checkbox = self._create_checkbox("Labels", True)
        self.show_labels_checkbox.stateChanged.connect(self.on_display_options_changed)
        display_options_layout.addWidget(self.show_labels_checkbox)

        # Checkbox: Tags
        self.show_tags_checkbox = self._create_checkbox("Tags", False)
        self.show_tags_checkbox.stateChanged.connect(self.on_display_options_changed)
        display_options_layout.addWidget(self.show_tags_checkbox)

        # Checkbox: Contenido
        self.show_content_checkbox = self._create_checkbox("Contenido", False)
        self.show_content_checkbox.stateChanged.connect(self.on_display_options_changed)
        display_options_layout.addWidget(self.show_content_checkbox)

        # Checkbox: Descripción
        self.show_description_checkbox = self._create_checkbox("Descripción", False)
        self.show_description_checkbox.stateChanged.connect(self.on_display_options_changed)
        display_options_layout.addWidget(self.show_description_checkbox)

        # Stretch
        display_options_layout.addStretch()

        main_layout.addWidget(self.display_options_widget)

        # ========== SEARCH BAR ==========
        search_widget = QWidget()
        search_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme.get_color('background_mid')};
                border-bottom: 1px solid {self.theme.get_color('surface')};
            }}
        """)
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(15, 8, 15, 8)
        search_layout.setSpacing(10)

        # Search icon
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_secondary')};
                font-size: 14pt;
            }}
        """)
        search_layout.addWidget(search_icon)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar items por nombre, contenido o descripción...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme.get_color('background_deep')};
                color: {self.theme.get_color('text_primary')};
                border: 1px solid {self.theme.get_color('surface')};
                border-radius: 0px;
                padding: 8px 12px;
                font-size: 10pt;
            }}
            QLineEdit:focus {{
                border-color: {self.theme.get_color('primary')};
            }}
            QLineEdit::placeholder {{
                color: {self.theme.get_color('text_secondary')};
            }}
        """)
        search_layout.addWidget(self.search_input)

        # Results counter
        self.results_label = QLabel("")
        self.results_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_secondary')};
                font-size: 9pt;
                padding-right: 5px;
            }}
        """)
        search_layout.addWidget(self.results_label)

        main_layout.addWidget(search_widget)

        # ========== ITEMS COUNT HEADER ==========
        self.items_count_label = QLabel(f"━━━ Items ({len(self.items)}) ━━━")
        self.items_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.items_count_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 10pt;
                font-weight: bold;
                padding: 8px;
                background-color: transparent;
            }
        """)
        main_layout.addWidget(self.items_count_label)

        # ========== SCROLL AREA FOR ITEMS ==========
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(f"""
            {PanelStyles.get_scroll_area_style()}
            {PanelStyles.get_scrollbar_style()}
        """)

        # Container for items
        self.items_container = QWidget()
        self.items_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        self.items_container.setStyleSheet(PanelStyles.get_body_style())

        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(
            PanelStyles.BODY_PADDING,
            PanelStyles.BODY_PADDING,
            PanelStyles.BODY_PADDING,
            PanelStyles.BODY_PADDING
        )
        self.items_layout.setSpacing(PanelStyles.ITEM_SPACING)
        self.items_layout.addStretch()

        self.scroll_area.setWidget(self.items_container)
        main_layout.addWidget(self.scroll_area)

        # ========== ACTIONS TOOLBAR (Bottom) ==========
        self.actions_widget = QWidget()
        self.actions_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme.get_color('background_mid')};
                border-top: 1px solid {self.theme.get_color('surface')};
            }}
        """)
        actions_layout = QHBoxLayout(self.actions_widget)
        actions_layout.setContentsMargins(10, 8, 10, 8)
        actions_layout.setSpacing(8)

        # Selection counter
        self.selection_label = QLabel("0 seleccionados")
        self.selection_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_secondary')};
                font-size: 9pt;
            }}
        """)
        actions_layout.addWidget(self.selection_label)

        actions_layout.addStretch()

        # Select All button
        self.select_all_button = QPushButton("Seleccionar todos")
        self.select_all_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.select_all_button.setStyleSheet(self._get_action_button_style())
        self.select_all_button.clicked.connect(self.select_all_items)
        actions_layout.addWidget(self.select_all_button)

        # Deselect All button
        self.deselect_all_button = QPushButton("Deseleccionar todos")
        self.deselect_all_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.deselect_all_button.setStyleSheet(self._get_action_button_style())
        self.deselect_all_button.clicked.connect(self.deselect_all_items)
        actions_layout.addWidget(self.deselect_all_button)

        # Favorite button
        self.favorite_button = QPushButton("⭐ Marcar favoritos")
        self.favorite_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.favorite_button.setStyleSheet(self._get_action_button_style())
        self.favorite_button.clicked.connect(self.mark_selected_as_favorite)
        self.favorite_button.setEnabled(False)
        self.favorite_button.setToolTip("Marcar items seleccionados como favoritos")
        actions_layout.addWidget(self.favorite_button)

        # Delete button
        self.delete_button = QPushButton("🗑️ Eliminar")
        self.delete_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.delete_button.setStyleSheet(self._get_action_button_style())
        self.delete_button.clicked.connect(self.delete_selected_items)
        self.delete_button.setEnabled(False)
        self.delete_button.setToolTip("Eliminar items seleccionados")
        actions_layout.addWidget(self.delete_button)

        # Copy selected button
        self.copy_selected_button = QPushButton("📋 Copiar")
        self.copy_selected_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.copy_selected_button.setStyleSheet(self._get_action_button_style(primary=True))
        self.copy_selected_button.clicked.connect(self.copy_selected_items)
        self.copy_selected_button.setEnabled(False)  # Disabled by default
        self.copy_selected_button.setToolTip("Copiar contenido de items seleccionados")
        actions_layout.addWidget(self.copy_selected_button)

        main_layout.addWidget(self.actions_widget)

        # Load items into the panel
        self.load_items()

    def _create_checkbox(self, text: str, checked: bool = False) -> QCheckBox:
        """Crear un checkbox con estilos consistentes"""
        checkbox = QCheckBox(text)
        checkbox.setChecked(checked)
        checkbox.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {self.theme.get_color('text_primary')};
                font-size: 9pt;
                spacing: 5px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {self.theme.get_color('primary')};
                border-radius: 0px;
                background-color: {self.theme.get_color('background_deep')};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.theme.get_color('primary')};
                border-color: {self.theme.get_color('primary')};
            }}
            QCheckBox::indicator:hover {{
                border-color: {self.theme.get_color('accent')};
            }}
        """)
        return checkbox

    def _get_action_button_style(self, primary: bool = False) -> str:
        """Obtener estilos para botones de acción"""
        if primary:
            bg_color = self.theme.get_color('success')
            hover_color = self.theme.get_color('secondary')
        else:
            bg_color = self.theme.get_color('background_deep')
            hover_color = self.theme.get_color('secondary')

        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {self.theme.get_color('text_primary')};
                border: 1px solid {self.theme.get_color('primary')};
                border-radius: 0px;
                padding: 6px 12px;
                font-size: 9pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {self.theme.get_color('accent')};
            }}
            QPushButton:disabled {{
                background-color: {self.theme.get_color('surface')};
                color: {self.theme.get_color('text_secondary')};
                border-color: {self.theme.get_color('surface')};
            }}
        """

    def load_items(self):
        """Cargar y mostrar los items en el panel"""
        logger.info(f"Loading {len(self.items)} related items for {self.entity_name}")

        # Clear existing items
        self.clear_items()

        # Add item cards
        for item in self.items:
            item_card = RelatedItemCard(
                item=item,
                show_labels=self.show_labels,
                show_tags=self.show_tags,
                show_content=self.show_content,
                show_description=self.show_description
            )
            item_card.checkbox_toggled.connect(self.on_item_selection_changed)
            item_card.copy_clicked.connect(self.on_item_copy_clicked)
            item_card.edit_requested.connect(self.on_item_edit_requested)

            self.items_layout.insertWidget(self.items_layout.count() - 1, item_card)

        logger.info(f"Successfully loaded {len(self.items)} items")

    def clear_items(self):
        """Limpiar todos los item cards del layout"""
        while self.items_layout.count() > 1:  # Keep the stretch at the end
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def on_search_changed(self, text: str):
        """Handle search text changes - filter items in real-time"""
        search_term = text.lower().strip()

        visible_count = 0
        total_count = 0

        # Iterate through all item cards
        for i in range(self.items_layout.count() - 1):  # -1 to skip stretch
            widget = self.items_layout.itemAt(i).widget()
            if isinstance(widget, RelatedItemCard):
                total_count += 1
                item = widget.item

                # Search in multiple fields
                if not search_term:
                    # No search - show all
                    widget.setVisible(True)
                    visible_count += 1
                else:
                    # Check if search term matches - asegurar que sea booleano
                    matches = False

                    # Buscar en label
                    if search_term in item.label.lower():
                        matches = True
                    # Buscar en content
                    elif item.content and search_term in item.content.lower():
                        matches = True
                    # Buscar en description
                    elif item.description and search_term in item.description.lower():
                        matches = True
                    # Buscar en tags
                    elif hasattr(item, 'tags') and item.tags:
                        for tag in item.tags:
                            if search_term in tag.lower():
                                matches = True
                                break

                    widget.setVisible(matches)
                    if matches:
                        visible_count += 1

        # Update results label
        if search_term:
            self.results_label.setText(f"{visible_count}/{total_count}")
            # Update items count header
            self.items_count_label.setText(f"━━━ Mostrando {visible_count} de {total_count} items ━━━")
        else:
            self.results_label.setText("")
            self.items_count_label.setText(f"━━━ Items ({total_count}) ━━━")

    def on_display_options_changed(self):
        """Handle changes in display options checkboxes"""
        self.show_labels = self.show_labels_checkbox.isChecked()
        self.show_tags = self.show_tags_checkbox.isChecked()
        self.show_content = self.show_content_checkbox.isChecked()
        self.show_description = self.show_description_checkbox.isChecked()

        logger.debug(f"Display options changed: labels={self.show_labels}, tags={self.show_tags}, "
                    f"content={self.show_content}, description={self.show_description}")

        # Clear selection
        self.selected_items.clear()
        self.update_selection_counter()

        # Reload items with new display options
        self.load_items()

        # Reapply search filter if active
        if self.search_input.text():
            self.on_search_changed(self.search_input.text())

    def on_item_selection_changed(self, item: Item, is_checked: bool):
        """Handle cuando cambia la selección de un item"""
        if is_checked:
            if item not in self.selected_items:
                self.selected_items.append(item)
        else:
            if item in self.selected_items:
                self.selected_items.remove(item)

        # Update selection counter
        self.update_selection_counter()

        # Emit signal
        self.selection_changed.emit(self.selected_items)

    def on_item_copy_clicked(self, item: Item):
        """Handle cuando se hace clic en copiar un item individual"""
        logger.info(f"Copy clicked for item: {item.label}")
        self.item_copied.emit(item)

    def on_item_edit_requested(self, item: Item):
        """Handle cuando se hace doble click para editar un item"""
        logger.info(f"Edit requested for item: {item.label}")
        self.item_edit_requested.emit(item)

    def update_selection_counter(self):
        """Actualizar el contador de items seleccionados"""
        count = len(self.selected_items)
        self.selection_label.setText(f"{count} seleccionado{'s' if count != 1 else ''}")

        # Enable/disable action buttons
        has_selection = count > 0
        self.copy_selected_button.setEnabled(has_selection)
        self.favorite_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def select_all_items(self):
        """Seleccionar todos los items"""
        for i in range(self.items_layout.count() - 1):  # -1 to skip stretch
            widget = self.items_layout.itemAt(i).widget()
            if isinstance(widget, RelatedItemCard):
                widget.set_checked(True)

    def deselect_all_items(self):
        """Deseleccionar todos los items"""
        for i in range(self.items_layout.count() - 1):
            widget = self.items_layout.itemAt(i).widget()
            if isinstance(widget, RelatedItemCard):
                widget.set_checked(False)

    def copy_selected_items(self):
        """Copiar todos los items seleccionados al portapapeles"""
        if not self.selected_items:
            return

        from PyQt6.QtWidgets import QApplication

        # Collect contents
        contents = []
        for item in self.selected_items:
            if item.content:
                contents.append(f"{item.label}: {item.content}")

        if contents:
            combined = "\n\n".join(contents)
            clipboard = QApplication.clipboard()
            clipboard.setText(combined)

            logger.info(f"Copied {len(self.selected_items)} items to clipboard")

            # Visual feedback
            original_text = self.copy_selected_button.text()
            self.copy_selected_button.setText("✅ Copiado!")
            QTimer.singleShot(1500, lambda: self.copy_selected_button.setText(original_text))

    def mark_selected_as_favorite(self):
        """Marcar items seleccionados como favoritos"""
        if not self.selected_items:
            return

        from PyQt6.QtWidgets import QMessageBox

        # Preguntar si marcar o desmarcar
        reply = QMessageBox.question(
            self,
            "Marcar como favoritos",
            f"¿Marcar {len(self.selected_items)} item(s) como favoritos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            item_ids = [int(item.id) for item in self.selected_items]

            # Emitir señal para que el padre maneje la actualización en BD
            self.items_favorited.emit(item_ids, True)

            logger.info(f"Marked {len(item_ids)} items as favorite")

            # Visual feedback
            original_text = self.favorite_button.text()
            self.favorite_button.setText("✅ Marcados!")
            QTimer.singleShot(1500, lambda: self.favorite_button.setText(original_text))

    def delete_selected_items(self):
        """Eliminar items seleccionados"""
        if not self.selected_items:
            return

        from PyQt6.QtWidgets import QMessageBox

        # Confirmación
        reply = QMessageBox.warning(
            self,
            "Eliminar items",
            f"¿Estás seguro de eliminar {len(self.selected_items)} item(s)?\n\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            item_ids = [int(item.id) for item in self.selected_items]

            # Emitir señal para que el padre maneje la eliminación en BD
            self.items_deleted.emit(item_ids)

            logger.info(f"Deleted {len(item_ids)} items")

            # Remover items de la lista local
            for item in self.selected_items:
                if item in self.items:
                    self.items.remove(item)

            # Limpiar selección y recargar
            self.selected_items.clear()
            self.update_selection_counter()
            self.load_items()

            # Visual feedback
            QMessageBox.information(
                self,
                "Items eliminados",
                f"Se eliminaron {len(item_ids)} item(s) correctamente."
            )

    def toggle_pin(self):
        """Toggle pin state (visual only for now)"""
        # TODO: Implement actual pinning logic if needed
        logger.info("Pin toggled")

    def toggle_minimize(self):
        """Minimizar el panel - lo agrega al gestor avanzado de barra de tareas"""
        from src.core.advanced_taskbar_manager import get_advanced_taskbar

        # Obtener gestor avanzado de taskbar
        taskbar = get_advanced_taskbar()

        # Ocultar panel
        self.hide()

        # Agregar a la barra de tareas avanzada
        taskbar.add_minimized_window(self)

        logger.info(f"Panel minimizado a taskbar avanzada: {self.entity_name}")

    def toggle_maximize(self):
        """Maximizar/restaurar el panel"""
        if self.is_maximized:
            # Restore
            if self.normal_geometry:
                self.setGeometry(self.normal_geometry)
            self.is_maximized = False
            self.maximize_button.setText("□")
            self.maximize_button.setToolTip("Maximizar panel")
        else:
            # Maximize
            self.normal_geometry = self.geometry()
            from PyQt6.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
            if screen:
                screen_rect = screen.availableGeometry()
                self.setGeometry(screen_rect)
            self.is_maximized = True
            self.maximize_button.setText("❐")
            self.maximize_button.setToolTip("Restaurar panel")

    def mousePressEvent(self, event):
        """Handle mouse press for window dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is on header (for dragging)
            if self.header_widget.geometry().contains(event.pos()):
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self.drag_position = None
        # Guardar posición después de mover
        self._schedule_save_state()

    def resizeEvent(self, event):
        """Handle resize event"""
        super().resizeEvent(event)
        # Guardar tamaño después de redimensionar
        self._schedule_save_state()

    def _schedule_save_state(self):
        """Programar guardado de estado con debounce (500ms)"""
        if self.db_manager:
            self.save_state_timer.start(500)

    def _save_state_to_db(self):
        """Guardar el estado actual del panel en la BD"""
        if not self.db_manager:
            return

        try:
            panel_type = self.relation_type.value  # 'tag', 'category', 'list'

            self.db_manager.save_floating_panel_state(
                panel_type=panel_type,
                entity_id=self.entity_id,
                position_x=self.x(),
                position_y=self.y(),
                width=self.width(),
                height=self.height(),
                is_maximized=self.is_maximized
            )
            logger.debug(f"Saved panel state: {panel_type} - {self.entity_name}")
        except Exception as e:
            logger.error(f"Error saving panel state: {e}")

    def _restore_state_from_db(self):
        """Restaurar el estado guardado del panel desde la BD"""
        if not self.db_manager:
            return

        try:
            panel_type = self.relation_type.value
            state = self.db_manager.get_floating_panel_state(panel_type, self.entity_id)

            if state:
                # Restaurar posición
                if state.get('position_x') is not None and state.get('position_y') is not None:
                    self.move(state['position_x'], state['position_y'])

                # Restaurar tamaño
                if state.get('width') and state.get('height'):
                    self.resize(state['width'], state['height'])

                # Restaurar estado maximizado
                if state.get('is_maximized'):
                    self.toggle_maximize()

                logger.info(f"Restored panel state: {panel_type} - {self.entity_name}")
        except Exception as e:
            logger.error(f"Error restoring panel state: {e}")

    def _setup_shadow_effect(self):
        """Configurar efecto de sombra para ventana frameless"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.setGraphicsEffect(shadow)

    def _animate_entrance(self):
        """Animación de entrada con fade in"""
        # Empezar con opacidad 0
        self.setWindowOpacity(0.0)

        # Crear animación
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)  # 300ms
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(0.98)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Iniciar animación
        self.fade_animation.start()

    def _get_enhanced_panel_style(self) -> str:
        """Obtener estilos mejorados del panel con gradientes y efectos"""
        return f"""
            QWidget {{
                background-color: {self.theme.get_color('background_deep')};
                color: {self.theme.get_color('text_primary')};
                border: 1px solid {self.theme.get_color('primary')};
                border-radius: 0px;
            }}

            /* Scroll Area mejorado */
            QScrollArea {{
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }}

            /* Scrollbar vertical personalizado */
            QScrollBar:vertical {{
                background-color: {self.theme.get_color('background_mid')};
                width: 10px;
                border-radius: 0px;
                margin: 0px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {self.theme.get_color('primary')};
                min-height: 30px;
                border-radius: 0px;
                margin: 0px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {self.theme.get_color('accent')};
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
            }}

            /* Scrollbar horizontal */
            QScrollBar:horizontal {{
                background-color: {self.theme.get_color('background_mid')};
                height: 10px;
                border-radius: 0px;
                margin: 0px;
            }}

            QScrollBar::handle:horizontal {{
                background-color: {self.theme.get_color('primary')};
                min-width: 30px;
                border-radius: 0px;
                margin: 0px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background-color: {self.theme.get_color('accent')};
            }}

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}

            /* Botones mejorados */
            QPushButton {{
                background-color: {self.theme.get_color('surface')};
                color: {self.theme.get_color('text_primary')};
                border: 1px solid {self.theme.get_color('primary')};
                border-radius: 0px;
                padding: 8px 16px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: {self.theme.get_color('primary')};
                border-color: {self.theme.get_color('accent')};
            }}

            QPushButton:pressed {{
                background-color: {self.theme.get_color('accent')};
            }}

            QPushButton:disabled {{
                background-color: {self.theme.get_color('surface')};
                color: {self.theme.get_color('text_secondary')};
                border-color: {self.theme.get_color('surface')};
            }}

            /* Labels mejorados */
            QLabel {{
                background-color: transparent;
                color: {self.theme.get_color('text_primary')};
            }}

            /* Checkboxes mejorados */
            QCheckBox {{
                spacing: 8px;
                color: {self.theme.get_color('text_primary')};
            }}

            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {self.theme.get_color('primary')};
                border-radius: 0px;
                background-color: {self.theme.get_color('background_deep')};
            }}

            QCheckBox::indicator:checked {{
                background-color: {self.theme.get_color('primary')};
                border-color: {self.theme.get_color('primary')};
                image: url(none);
            }}

            QCheckBox::indicator:hover {{
                border-color: {self.theme.get_color('accent')};
                background-color: {self.theme.get_color('surface')};
            }}

            QCheckBox::indicator:checked:hover {{
                background-color: {self.theme.get_color('accent')};
            }}
        """

    def closeEvent(self, event):
        """Handle close event"""
        # Remover de la barra de tareas avanzada si está ahí
        try:
            from src.core.advanced_taskbar_manager import get_advanced_taskbar
            taskbar = get_advanced_taskbar()
            taskbar.remove_minimized_window(self)
        except Exception as e:
            logger.debug(f"Error removing from taskbar: {e}")

        # Guardar estado final antes de cerrar
        self._save_state_to_db()
        self.panel_closed.emit()
        event.accept()

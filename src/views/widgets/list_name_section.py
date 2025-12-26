"""
List Selector Section
Selector de lista existente o creación de nueva lista
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFrame
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class ListNameSection(QWidget):
    """
    Sección para seleccionar lista existente o crear nueva

    Características:
    - Selector (QComboBox) de listas relacionadas con tag de proyecto/área
    - Botón + para crear nueva lista
    - Siempre visible
    - Obligatorio para guardar

    Señales:
        list_changed(int, str): Emitida cuando cambia la lista seleccionada (list_id, list_name)
        create_list_clicked(): Emitida cuando se hace clic en el botón +
    """

    # Señales
    list_changed = pyqtSignal(object, str)  # (list_id or None, list_name)
    create_list_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

    def _setup_ui(self):
        """Configura la interfaz"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("📝 Lista")
        header_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header_label.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(header_label)

        # Badge obligatorio
        required_badge = QLabel("*")
        required_badge.setStyleSheet("color: #FF5252; font-size: 14px; font-weight: bold;")
        required_badge.setToolTip("Campo obligatorio")
        header_layout.addWidget(required_badge)

        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # Selector de lista con botón +
        field_layout = QHBoxLayout()
        field_layout.setSpacing(6)

        # Label
        label = QLabel("Lista:")
        label.setFixedWidth(80)
        label.setStyleSheet("color: #cccccc; font-size: 11px;")
        field_layout.addWidget(label)

        # ComboBox
        self.list_combo = QComboBox()
        self.list_combo.setPlaceholderText("Seleccionar lista...")
        self.list_combo.setMinimumHeight(30)
        field_layout.addWidget(self.list_combo, 1)

        # Botón crear lista
        self.create_btn = QPushButton("+")
        self.create_btn.setFixedSize(30, 30)
        self.create_btn.setToolTip("Crear nueva lista")
        field_layout.addWidget(self.create_btn)

        main_layout.addLayout(field_layout)

    def _apply_styles(self):
        """Aplica estilos CSS"""
        self.setStyleSheet("""
            ListNameSection {
                background-color: #252525;
                border-radius: 6px;
            }
            QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }
            QComboBox:hover {
                background-color: #353535;
            }
            QComboBox:focus {
                border: 1px solid #2196F3;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #888;
                width: 0;
                height: 0;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #ffffff;
                selection-background-color: #2196F3;
                border: 1px solid #444;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QLabel {
                color: #ffffff;
                font-size: 11px;
            }
        """)

    def _connect_signals(self):
        """Conecta señales internas"""
        self.list_combo.currentIndexChanged.connect(self._on_list_changed)
        self.create_btn.clicked.connect(self.create_list_clicked.emit)

    def _on_list_changed(self, index: int):
        """Callback cuando cambia la selección"""
        list_id = self.get_selected_list_id()
        list_name = self.get_name()
        self.list_changed.emit(list_id, list_name)
        logger.debug(f"Lista seleccionada: {list_name} (ID: {list_id})")

    def load_lists(self, lists: list[tuple[int, str]], include_new_option: bool = True):
        """
        Carga listas en el selector

        Args:
            lists: Lista de tuplas (id, name)
            include_new_option: Si incluir opción "Nueva lista..." al inicio
        """
        self.list_combo.clear()

        if include_new_option:
            self.list_combo.addItem("➕ Nueva lista...", None)

        for list_id, list_name in lists:
            self.list_combo.addItem(list_name, list_id)

        logger.debug(f"Cargadas {len(lists)} listas en selector")

    def get_selected_list_id(self) -> int | None:
        """
        Obtiene el ID de la lista seleccionada

        Returns:
            ID de la lista o None si es nueva lista
        """
        return self.list_combo.currentData()

    def get_name(self) -> str:
        """
        Obtiene el nombre de la lista seleccionada

        Returns:
            Nombre de la lista o "" si no hay selección válida
        """
        if self.list_combo.currentIndex() < 0:
            return ""

        text = self.list_combo.currentText()
        # Si es la opción "Nueva lista...", retornar vacío
        if text.startswith("➕"):
            return ""

        return text.strip()

    def set_list_by_id(self, list_id: int | None):
        """
        Establece la lista seleccionada por ID

        Args:
            list_id: ID de la lista a seleccionar
        """
        if list_id is None:
            self.list_combo.setCurrentIndex(0)  # Nueva lista
            return

        index = self.list_combo.findData(list_id)
        if index >= 0:
            self.list_combo.setCurrentIndex(index)
        else:
            logger.warning(f"No se encontró lista con ID {list_id}")
            self.list_combo.setCurrentIndex(0)

    def set_name(self, name: str):
        """
        Establece la lista por nombre (compatibilidad con versión anterior)

        Args:
            name: Nombre de la lista
        """
        if not name:
            self.list_combo.setCurrentIndex(0)
            return

        # Buscar por texto
        index = self.list_combo.findText(name)
        if index >= 0:
            self.list_combo.setCurrentIndex(index)
        else:
            logger.debug(f"No se encontró lista con nombre '{name}', seleccionando 'Nueva lista'")
            self.list_combo.setCurrentIndex(0)

    def add_and_select_list(self, list_id: int, list_name: str):
        """
        Agrega una nueva lista al selector y la selecciona

        Args:
            list_id: ID de la nueva lista
            list_name: Nombre de la nueva lista
        """
        # Agregar al combo
        self.list_combo.addItem(list_name, list_id)

        # Seleccionar la lista recién agregada
        index = self.list_combo.findData(list_id)
        if index >= 0:
            self.list_combo.setCurrentIndex(index)
            logger.info(f"Lista '{list_name}' agregada y seleccionada")

    def clear(self):
        """Limpia la selección"""
        self.list_combo.setCurrentIndex(0)

    def is_new_list_mode(self) -> bool:
        """
        Verifica si está en modo "Nueva lista"

        Returns:
            True si no hay lista seleccionada (modo crear nueva)
        """
        return self.get_selected_list_id() is None

    def validate(self) -> tuple[bool, str]:
        """
        Valida la selección de lista

        Returns:
            Tupla (is_valid, error_message)
        """
        # Verificar que haya una selección válida
        if self.list_combo.currentIndex() < 0:
            return False, "Debe seleccionar una lista"

        # Si está en modo "Nueva lista", es válido (se creará después)
        if self.is_new_list_mode():
            return True, ""

        # Si hay lista seleccionada, validar que tenga nombre
        list_name = self.get_name()
        if not list_name:
            return False, "Debe seleccionar una lista válida"

        return True, ""

"""
Widget de selección de contexto COMPACTO para el Visor de Proyectos/Áreas

Componentes:
- Selector de Proyecto (dropdown + botón crear)
- Selector de Área (dropdown + botón crear)

CRÍTICO: Proyecto y Área son MUTUAMENTE EXCLUYENTES
- Al seleccionar Proyecto → Área se resetea a "Ninguno"
- Al seleccionar Área → Proyecto se resetea a "Seleccionar proyecto..."

Señales:
- project_changed(int): Emitida cuando se selecciona un proyecto
- area_changed(int): Emitida cuando se selecciona un área
- create_project_clicked: Emitida cuando se hace click en "+ Proyecto"
- create_area_clicked: Emitida cuando se hace click en "+ Área"

Versión: 1.1
Fecha: 2025-12-26
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame, QPushButton,
    QCompleter
)
from PyQt6.QtCore import pyqtSignal, Qt, QObject, QEvent
from PyQt6.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class PopupPositionFilter(QObject):
    """
    Event filter para ajustar la posición del popup del completer
    cuando se muestra, asegurando que esté dentro de los límites de la pantalla
    """

    def __init__(self, combo, completer=None, parent=None):
        super().__init__(parent)
        self.combo = combo
        self.completer = completer
        self.is_combo_view = completer is None
        self._adjusting = False  # Bandera para prevenir loops infinitos

    def eventFilter(self, obj, event):
        """Filtra eventos del popup para ajustar su posición al mostrarse o moverse"""
        event_type = event.type()

        if not self._adjusting:
            if event_type == QEvent.Type.Show:
                # Cuando se muestra por primera vez, ajustar posición
                self.adjust_popup_position(obj)
            elif event_type == QEvent.Type.Move:
                # Interceptar el movimiento y aplicar nuestra propia posición
                self.adjust_popup_position(obj)
                # CRÍTICO: Prevenir que el evento Move se propague para evitar
                # que el popup se mueva a la posición incorrecta
                return True
            elif event_type == QEvent.Type.Resize:
                # Al cambiar tamaño, reajustar posición
                self.adjust_popup_position(obj)

        return super().eventFilter(obj, event)

    def adjust_popup_position(self, popup_widget):
        """Ajusta la posición del popup para que esté dentro de la ventana"""
        # Si es el popup del completer, obtenerlo del completer
        if not self.is_combo_view and self.completer:
            popup_widget = self.completer.popup()

        if not popup_widget or not popup_widget.isVisible():
            return

        # Ajustar la posición inmediatamente
        self._do_adjust_position(popup_widget)

    def _do_adjust_position(self, popup_widget):
        """Realiza el ajuste real de posición"""
        from PyQt6.QtGui import QGuiApplication

        if not popup_widget or not popup_widget.isVisible():
            return

        # Activar bandera para prevenir loops
        self._adjusting = True

        try:
            # Obtener la geometría del combobox en coordenadas globales
            combo_rect = self.combo.rect()
            combo_bottom_left = self.combo.mapToGlobal(combo_rect.bottomLeft())
            combo_bottom_right = self.combo.mapToGlobal(combo_rect.bottomRight())

            # Obtener el ancho del popup
            popup_width = popup_widget.width()
            if popup_width < 100:
                popup_width = max(popup_widget.sizeHint().width(), self.combo.width())

            # Obtener la geometría de la pantalla donde está el widget
            screen = QGuiApplication.screenAt(combo_bottom_left)
            if screen:
                screen_geometry = screen.availableGeometry()
            else:
                # Fallback: usar la pantalla principal
                screen_geometry = QGuiApplication.primaryScreen().availableGeometry()

            # Calcular posición X (alineado con el combo)
            x_pos = combo_bottom_left.x()

            # Si el popup se sale por la derecha, ajustarlo
            if x_pos + popup_width > screen_geometry.right():
                x_pos = combo_bottom_right.x() - popup_width

            # Si aún se sale por la izquierda, alinearlo con el borde izquierdo de la pantalla
            if x_pos < screen_geometry.left():
                x_pos = screen_geometry.left()

            # Posicionar el popup SOLO si es necesario (para evitar loops)
            current_pos = popup_widget.pos()
            new_pos_y = combo_bottom_left.y()

            if current_pos.x() != x_pos or current_pos.y() != new_pos_y:
                popup_widget.move(x_pos, new_pos_y)

            # Ajustar ancho si es necesario
            if popup_widget.width() < self.combo.width():
                popup_widget.setMinimumWidth(self.combo.width())

        finally:
            # Desactivar bandera
            self._adjusting = False


class ContextSelectorCompact(QWidget):
    """
    Widget compacto para seleccionar Proyecto o Área (MUTUAMENTE EXCLUYENTES)

    Permite seleccionar elementos existentes y crear nuevos mediante botones "+".

    Señales:
        project_changed(int): ID del proyecto seleccionado (o None)
        area_changed(int): ID del área seleccionada (o None)
        create_project_clicked: Solicitud de crear proyecto
        create_area_clicked: Solicitud de crear área
    """

    # Señales
    project_changed = pyqtSignal(object)  # int or None
    area_changed = pyqtSignal(object)  # int or None
    create_project_clicked = pyqtSignal()
    create_area_clicked = pyqtSignal()

    def __init__(self, parent=None):
        """
        Inicializa el selector compacto

        Args:
            parent: Widget padre
        """
        super().__init__(parent)

        # Estado interno
        self._block_signals = False  # Para evitar bucles al resetear

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

        logger.debug("ContextSelectorCompact inicializado")

    def _setup_ui(self):
        """Configura la interfaz del widget"""
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Header de la sección
        header = QLabel("📋 Contexto")
        header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header.setStyleSheet("color: #00BFFF; margin-bottom: 5px;")
        layout.addWidget(header)

        # Frame contenedor
        container = QFrame()
        container.setObjectName("contextContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(10)

        # Fila de Proyecto
        project_row_layout, self.project_combo, self.create_project_btn = self._create_selector_row(
            "Proyecto", "Seleccionar proyecto..."
        )
        container_layout.addLayout(project_row_layout)

        # Fila de Área
        area_row_layout, self.area_combo, self.create_area_btn = self._create_selector_row(
            "Área", "Ninguno"
        )
        container_layout.addLayout(area_row_layout)

        layout.addWidget(container)

        # Conectar botones de creación
        self.create_project_btn.clicked.connect(self.create_project_clicked.emit)
        self.create_area_btn.clicked.connect(self.create_area_clicked.emit)

    def _create_selector_row(self, label_text: str, placeholder: str):
        """
        Crea una fila con etiqueta + combobox + botón crear

        Args:
            label_text: Texto de la etiqueta
            placeholder: Texto del placeholder

        Returns:
            tuple: (QHBoxLayout, QComboBox, QPushButton)
        """
        row = QHBoxLayout()
        row.setSpacing(8)

        # Etiqueta
        label = QLabel(label_text)
        label.setFixedWidth(70)
        label.setStyleSheet("""
            color: #ffffff;
            font-size: 11px;
            font-weight: 500;
        """)

        # ComboBox
        combo = QComboBox()
        combo.setPlaceholderText(placeholder)
        combo.setMinimumHeight(32)
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        # Configurar autocompletado (Buscador)
        completer = combo.completer()
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

        # Estilizar el popup del autocompletado para que coincida con el tema
        popup = completer.popup()
        popup.setStyleSheet("""
            QAbstractItemView {
                background-color: #3d3d3d;
                color: #ffffff;
                selection-background-color: #00BFFF;
                selection-color: #ffffff;
                border: 1px solid #555;
                outline: 0;
            }
            QAbstractItemView::item:hover {
                background-color: #4d4d4d;
                color: #00BFFF;
            }
        """)

        # Configurar el popup del QComboBox para que se muestre correctamente
        combo_view = combo.view()
        combo_view.setStyleSheet("""
            QAbstractItemView {
                background-color: #3d3d3d;
                color: #ffffff;
                selection-background-color: #00BFFF;
                selection-color: #ffffff;
                border: 1px solid #555;
                outline: 0;
            }
            QAbstractItemView::item {
                padding: 5px;
            }
            QAbstractItemView::item:hover {
                background-color: #4d4d4d;
                color: #00BFFF;
            }
        """)

        # Forzar que el popup se abra dentro de la ventana
        combo_view.window().setWindowFlags(
            combo_view.window().windowFlags() | Qt.WindowType.Popup
        )

        # Instalar event filter para ajustar posición del popup del completer
        popup_filter_completer = PopupPositionFilter(combo, completer, combo)
        completer.popup().installEventFilter(popup_filter_completer)

        # Instalar event filter para el popup del QComboBox también
        popup_filter_combo = PopupPositionFilter(combo, None, combo)
        combo_view.window().installEventFilter(popup_filter_combo)

        # Guardar referencias a los filters para evitar que sean recolectados por el GC
        combo._popup_filter_completer = popup_filter_completer
        combo._popup_filter_combo = popup_filter_combo

        # Botón "+" para crear
        create_btn = QPushButton("+")
        create_btn.setFixedSize(32, 32)
        create_btn.setToolTip(f"Crear nuevo {label_text.lower()}")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d5d2e;
                color: #00ff88;
                border: 2px solid #00ff88;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a7a3c;
                border-color: #7CFC00;
            }
            QPushButton:pressed {
                background-color: #1a4d2e;
            }
        """)

        row.addWidget(label)
        row.addWidget(combo, 1)  # Stretch factor 1
        row.addWidget(create_btn)

        return (row, combo, create_btn)

    def _apply_styles(self):
        """Aplica estilos CSS al widget"""
        self.setStyleSheet("""
            QFrame#contextContainer {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 6px;
            }

            QComboBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 11px;
            }

            QComboBox:hover {
                border-color: #00BFFF;
                background-color: #4d4d4d;
            }

            QComboBox:focus {
                border-color: #00BFFF;
            }

            QComboBox::drop-down {
                border: none;
                width: 20px;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #999;
                margin-right: 5px;
            }

            QComboBox::down-arrow:hover {
                border-top-color: #00BFFF;
            }

            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                color: #ffffff;
                selection-background-color: #00BFFF;
                selection-color: #ffffff;
                selection-color: #ffffff;
                border: 1px solid #555;
            }

            QComboBox QLineEdit {
                background-color: transparent;
                color: #ffffff;
                border: none;
                selection-background-color: #00BFFF;
                selection-color: #ffffff;
            }
        """)

    def _connect_signals(self):
        """Conecta señales internas"""
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)
        self.area_combo.currentIndexChanged.connect(self._on_area_changed)

    # === CALLBACKS INTERNOS ===

    def _on_project_changed(self, index: int):
        """
        Callback cuando cambia la selección de proyecto

        CRÍTICO: Resetea área automáticamente (mutuamente excluyente)

        Args:
            index: Índice seleccionado en el combobox
        """
        if self._block_signals:
            return

        project_id = self.project_combo.currentData()

        if project_id:
            # OBLIGATORIO: Resetear área cuando se selecciona proyecto
            self.reset_area()
            logger.info(f"Proyecto seleccionado: {project_id} - Área reseteada")

            # Emitir señal
            self.project_changed.emit(project_id)
        else:
            # Se seleccionó placeholder
            logger.debug("Proyecto deseleccionado")
            self.project_changed.emit(None)

    def _on_area_changed(self, index: int):
        """
        Callback cuando cambia la selección de área

        CRÍTICO: Resetea proyecto automáticamente (mutuamente excluyente)

        Args:
            index: Índice seleccionado en el combobox
        """
        if self._block_signals:
            return

        area_id = self.area_combo.currentData()

        if area_id:
            # OBLIGATORIO: Resetear proyecto cuando se selecciona área
            self.reset_project()
            logger.info(f"Área seleccionada: {area_id} - Proyecto reseteado")

            # Emitir señal
            self.area_changed.emit(area_id)
        else:
            # Se seleccionó placeholder
            logger.debug("Área deseleccionada")
            self.area_changed.emit(None)

    # === MÉTODOS PÚBLICOS ===

    def load_projects(self, projects: list):
        """
        Cargar lista de proyectos en el dropdown

        Args:
            projects: Lista de tuplas [(id, name), ...]
        """
        logger.debug(f"🔄 load_projects() recibió: {projects}")
        logger.debug(f"🔄 Longitud: {len(projects)}")

        self._block_signals = True
        self.project_combo.clear()
        logger.debug("🔄 ComboBox limpiado")

        # Agregar placeholder
        self.project_combo.addItem("Seleccionar proyecto...", None)
        logger.debug("🔄 Placeholder agregado")

        # Agregar proyectos
        for project_id, project_name in projects:
            self.project_combo.addItem(project_name, project_id)
            logger.debug(f"🔄 Agregado: {project_name} (ID: {project_id})")

        self._block_signals = False
        logger.debug(f"✅ ComboBox tiene {self.project_combo.count()} items totales")

        # Log de todos los items
        for i in range(self.project_combo.count()):
            logger.debug(f"  Item {i}: {self.project_combo.itemText(i)} -> {self.project_combo.itemData(i)}")

    def load_areas(self, areas: list):
        """
        Cargar lista de áreas en el dropdown

        Args:
            areas: Lista de tuplas [(id, name), ...]
        """
        logger.debug(f"🔄 load_areas() recibió: {areas}")
        logger.debug(f"🔄 Longitud: {len(areas)}")

        self._block_signals = True
        self.area_combo.clear()
        logger.debug("🔄 ComboBox limpiado")

        # Agregar placeholder
        self.area_combo.addItem("Ninguno", None)
        logger.debug("🔄 Placeholder agregado")

        # Agregar áreas
        for area_id, area_name in areas:
            self.area_combo.addItem(area_name, area_id)
            logger.debug(f"🔄 Agregado: {area_name} (ID: {area_id})")

        self._block_signals = False
        logger.debug(f"✅ ComboBox tiene {self.area_combo.count()} items totales")

        # Log de todos los items
        for i in range(self.area_combo.count()):
            logger.debug(f"  Item {i}: {self.area_combo.itemText(i)} -> {self.area_combo.itemData(i)}")

    def get_selected_project_id(self):
        """
        Obtener ID del proyecto seleccionado

        Returns:
            int or None: ID del proyecto o None si no hay selección
        """
        return self.project_combo.currentData()

    def get_selected_area_id(self):
        """
        Obtener ID del área seleccionada

        Returns:
            int or None: ID del área o None si no hay selección
        """
        return self.area_combo.currentData()

    def reset_project(self):
        """
        Resetear selector de proyecto al placeholder

        Bloquea señales para evitar bucles al ser llamado desde _on_area_changed.
        """
        self._block_signals = True
        self.project_combo.setCurrentIndex(0)  # Placeholder
        self._block_signals = False
        logger.debug("Proyecto reseteado a placeholder")

    def reset_area(self):
        """
        Resetear selector de área al placeholder

        Bloquea señales para evitar bucles al ser llamado desde _on_project_changed.
        """
        self._block_signals = True
        self.area_combo.setCurrentIndex(0)  # Placeholder
        self._block_signals = False
        logger.debug("Área reseteada a placeholder")

    def has_project_selected(self) -> bool:
        """
        Verificar si hay un proyecto seleccionado

        Returns:
            bool: True si hay proyecto seleccionado, False si no
        """
        return self.get_selected_project_id() is not None

    def has_area_selected(self) -> bool:
        """
        Verificar si hay un área seleccionada

        Returns:
            bool: True si hay área seleccionada, False si no
        """
        return self.get_selected_area_id() is not None

    def validate_exclusivity(self) -> bool:
        """
        Validar que Proyecto y Área sean mutuamente excluyentes

        Returns:
            bool: True si la validación pasa (solo uno o ninguno seleccionado)

        Raises:
            AssertionError: Si ambos están seleccionados (no debería pasar)
        """
        has_project = self.has_project_selected()
        has_area = self.has_area_selected()

        # CRÍTICO: Nunca deben estar ambos seleccionados
        assert not (has_project and has_area), \
            "ERROR: Proyecto y Área no pueden estar seleccionados simultáneamente"

        return True


# === TEST ===
if __name__ == '__main__':
    """Test independiente del widget"""
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Crear widget
    widget = ContextSelectorCompact()

    # Cargar datos de prueba
    widget.load_projects([
        (1, "Proyecto Backend"),
        (2, "Proyecto Frontend"),
        (3, "Proyecto Mobile"),
    ])

    widget.load_areas([
        (1, "Área Desarrollo"),
        (2, "Área Testing"),
        (3, "Área DevOps"),
    ])

    # Conectar señales para testing
    widget.project_changed.connect(
        lambda pid: print(f"✓ Proyecto cambiado: {pid}")
    )
    widget.area_changed.connect(
        lambda aid: print(f"✓ Área cambiada: {aid}")
    )

    # Mostrar widget
    widget.setMinimumWidth(400)
    widget.show()

    sys.exit(app.exec())

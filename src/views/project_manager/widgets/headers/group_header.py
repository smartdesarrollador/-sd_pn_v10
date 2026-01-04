"""
Widget de encabezado de grupo de items para vista completa

Muestra el nombre del grupo (categoría, lista o tag de items).
Para listas, incluye botón "+" para crear lista.

Autor: Widget Sidebar Team
Versión: 1.1
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from ...styles.full_view_styles import FullViewStyles
import pyperclip


class GroupHeaderWidget(QFrame):
    """
    Widget de encabezado de grupo de items

    Nivel 3 de jerarquía: Muestra el nombre del grupo de items
    (categoría, lista o tag de items).

    Para listas, incluye botón "+" para crear nueva lista.

    Señales:
        create_list_clicked: Emitida cuando se hace click en el botón "+" (solo para listas)
    """

    # Señales
    create_list_clicked = pyqtSignal()

    def __init__(self, parent=None):
        """
        Inicializar widget de encabezado de grupo

        Args:
            parent: Widget padre
        """
        super().__init__(parent)

        self.group_name = ""
        self.group_type = "category"  # 'category', 'list', 'tag'
        self.create_list_btn = None  # Solo para listas
        self.copy_list_name_btn = None  # Solo para listas

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """Inicializar interfaz de usuario"""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(30, 5, 10, 5)
        self.layout.setSpacing(8)

        # Título del grupo
        self.title_label = QLabel()
        self.title_label.setObjectName("group_title")
        self.layout.addWidget(self.title_label)

        # Spacer para alinear a la izquierda
        self.layout.addStretch()

    def apply_styles(self):
        """Aplicar estilos CSS"""
        self.setStyleSheet(FullViewStyles.get_group_header_style())

    def set_group_info(self, name: str, group_type: str = "category"):
        """
        Establecer información del grupo

        Args:
            name: Nombre del grupo
            group_type: Tipo de grupo ('category', 'list', 'tag')
        """
        self.group_name = name
        self.group_type = group_type

        # Remover botones anteriores si existen
        if self.create_list_btn:
            self.create_list_btn.deleteLater()
            self.create_list_btn = None
        if self.copy_list_name_btn:
            self.copy_list_name_btn.deleteLater()
            self.copy_list_name_btn = None

        # Formato según tipo
        if group_type == "category":
            self.title_label.setText(f"[ Categoría: {name} ]")
        elif group_type == "list":
            # Limitar nombre a 20 caracteres con puntos suspensivos
            display_name = name if len(name) <= 20 else f"{name[:20]}..."
            self.title_label.setText(display_name)
            # Agregar tooltip con el nombre completo
            self.title_label.setToolTip(f"Lista: {name}")
            # Agregar botón de copiar nombre de lista
            self._add_copy_list_name_button()
            # Agregar botón "+" para crear lista
            self._add_create_list_button()
        elif group_type == "tag":
            self.title_label.setText(f"[ Tag: {name} ]")
        else:
            self.title_label.setText(f"[ {name} ]")

    def _add_create_list_button(self):
        """Agregar botón '+' para crear lista (solo cuando es tipo 'list')"""
        if self.create_list_btn:
            return  # Ya existe

        self.create_list_btn = QPushButton("+")
        self.create_list_btn.setFixedSize(24, 24)
        self.create_list_btn.setToolTip("Crear nueva lista")
        self.create_list_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_list_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d5d2e;
                color: #00ff88;
                border: 2px solid #00ff88;
                border-radius: 4px;
                font-size: 16px;
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
        self.create_list_btn.clicked.connect(self.create_list_clicked.emit)

        # Insertar botón antes del spacer
        self.layout.insertWidget(self.layout.count() - 1, self.create_list_btn)

    def _add_copy_list_name_button(self):
        """Agregar botón de copiar nombre de lista (solo cuando es tipo 'list')"""
        if self.copy_list_name_btn:
            return  # Ya existe

        self.copy_list_name_btn = QPushButton("📋")
        self.copy_list_name_btn.setFixedSize(24, 24)
        self.copy_list_name_btn.setToolTip("Copiar nombre de lista al portapapeles")
        self.copy_list_name_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_list_name_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 12px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
                border-color: #666;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
        """)
        self.copy_list_name_btn.clicked.connect(self._copy_list_name_to_clipboard)

        # Insertar botón antes del spacer
        self.layout.insertWidget(self.layout.count() - 1, self.copy_list_name_btn)

    def _copy_list_name_to_clipboard(self):
        """Copiar nombre de lista al portapapeles con feedback visual"""
        try:
            # Copiar al portapapeles
            pyperclip.copy(self.group_name)

            # Feedback visual: cambiar a verde temporalmente
            success_style = """
                QPushButton {
                    background-color: #4CAF50;
                    color: #ffffff;
                    border: 1px solid #45a049;
                    border-radius: 4px;
                    font-size: 12px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                    border-color: #3d8b40;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """

            # Cambiar a verde con checkmark
            self.copy_list_name_btn.setStyleSheet(success_style)
            self.copy_list_name_btn.setText("✓")

            # Restaurar después de 1.5 segundos
            QTimer.singleShot(1500, self._restore_copy_button_style)

        except Exception as e:
            print(f"Error al copiar nombre de lista: {e}")

    def _restore_copy_button_style(self):
        """Restaurar estilo original del botón de copiar"""
        original_style = """
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 12px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
                border-color: #666;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
        """
        if self.copy_list_name_btn:
            self.copy_list_name_btn.setStyleSheet(original_style)
            self.copy_list_name_btn.setText("📋")

    def get_group_name(self) -> str:
        """
        Obtener nombre del grupo

        Returns:
            Nombre del grupo
        """
        return self.group_name

    def get_group_type(self) -> str:
        """
        Obtener tipo del grupo

        Returns:
            Tipo del grupo ('category', 'list', 'tag')
        """
        return self.group_type

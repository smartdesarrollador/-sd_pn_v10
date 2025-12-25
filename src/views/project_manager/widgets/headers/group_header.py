"""
Widget de encabezado de grupo de items para vista completa

Muestra el nombre del grupo (categoría, lista o tag de items).

Autor: Widget Sidebar Team
Versión: 1.0
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from ...styles.full_view_styles import FullViewStyles


class GroupHeaderWidget(QFrame):
    """
    Widget de encabezado de grupo de items

    Nivel 3 de jerarquía: Muestra el nombre del grupo de items
    (categoría, lista o tag de items).
    """

    def __init__(self, parent=None):
        """
        Inicializar widget de encabezado de grupo

        Args:
            parent: Widget padre
        """
        super().__init__(parent)

        self.group_name = ""
        self.group_type = "category"  # 'category', 'list', 'tag'

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 5, 10, 5)
        layout.setSpacing(6)

        # Título del grupo
        self.title_label = QLabel()
        self.title_label.setObjectName("group_title")
        layout.addWidget(self.title_label)

        # Spacer para alinear a la izquierda
        layout.addStretch()

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

        # Formato según tipo
        if group_type == "category":
            self.title_label.setText(f"[ Categoría: {name} ]")
        elif group_type == "list":
            self.title_label.setText(f"[ Lista: {name} ]")
        elif group_type == "tag":
            self.title_label.setText(f"[ Tag: {name} ]")
        else:
            self.title_label.setText(f"[ {name} ]")

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

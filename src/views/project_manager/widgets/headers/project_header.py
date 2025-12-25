"""
Widget de encabezado de proyecto para vista completa

Muestra el nombre e icono del proyecto como título principal
de la vista completa.

Autor: Widget Sidebar Team
Versión: 1.0
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from ...styles.full_view_styles import FullViewStyles


class ProjectHeaderWidget(QFrame):
    """
    Widget de encabezado de proyecto

    Nivel 1 de jerarquía: Título principal que muestra
    el nombre e icono del proyecto.
    """

    def __init__(self, parent=None):
        """
        Inicializar widget de encabezado de proyecto

        Args:
            parent: Widget padre
        """
        super().__init__(parent)

        self.project_name = ""
        self.project_icon = "📁"

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Icono del proyecto
        self.icon_label = QLabel(self.project_icon)
        self.icon_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(self.icon_label)

        # Título del proyecto
        self.title_label = QLabel()
        self.title_label.setObjectName("project_title")
        layout.addWidget(self.title_label)

        # Spacer para alinear a la izquierda
        layout.addStretch()

    def apply_styles(self):
        """Aplicar estilos CSS"""
        self.setStyleSheet(FullViewStyles.get_project_header_style())

    def set_project_info(self, name: str, icon: str = "📁"):
        """
        Establecer información del proyecto

        Args:
            name: Nombre del proyecto
            icon: Emoji o icono del proyecto (por defecto: 📁)
        """
        self.project_name = name
        self.project_icon = icon

        # Actualizar UI
        self.title_label.setText(f"// {name}")
        self.icon_label.setText(icon)

    def get_project_name(self) -> str:
        """
        Obtener nombre del proyecto

        Returns:
            Nombre del proyecto
        """
        return self.project_name

    def get_project_icon(self) -> str:
        """
        Obtener icono del proyecto

        Returns:
            Icono del proyecto
        """
        return self.project_icon

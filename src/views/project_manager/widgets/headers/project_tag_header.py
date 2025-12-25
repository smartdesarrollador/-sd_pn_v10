"""
Widget de encabezado de tag de proyecto para vista completa

Muestra el nombre del tag de proyecto con funcionalidad de colapso/expansión.

Autor: Widget Sidebar Team
Versión: 1.0
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from ...styles.full_view_styles import FullViewStyles


class ProjectTagHeaderWidget(QFrame):
    """
    Widget de encabezado de tag de proyecto

    Nivel 2 de jerarquía: Muestra tags de proyecto con color personalizado,
    contador de items y funcionalidad de colapso/expansión.

    Señales:
        toggle_collapsed: Emitida cuando se cambia el estado de colapso
    """

    # Señales
    toggle_collapsed = pyqtSignal(bool)  # True = colapsado, False = expandido

    def __init__(self, parent=None):
        """
        Inicializar widget de encabezado de tag

        Args:
            parent: Widget padre
        """
        super().__init__(parent)

        self.tag_name = ""
        self.tag_color = "#32CD32"
        self.item_count = 0
        self.is_collapsed = False

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 6, 10, 6)
        layout.setSpacing(8)

        # Botón de colapso
        self.collapse_btn = QPushButton("▼")
        self.collapse_btn.setFixedSize(20, 20)
        self.collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        self.collapse_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #32CD32;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #7CFC00;
            }
        """)
        layout.addWidget(self.collapse_btn)

        # Icono de tag
        self.icon_label = QLabel("🏷️")
        self.icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.icon_label)

        # Título del tag
        self.title_label = QLabel()
        self.title_label.setObjectName("tag_title")
        layout.addWidget(self.title_label)

        # Contador de items
        self.count_label = QLabel()
        self.count_label.setObjectName("tag_count")
        layout.addWidget(self.count_label)

        # Spacer para alinear a la izquierda
        layout.addStretch()

    def apply_styles(self):
        """Aplicar estilos CSS"""
        self.setStyleSheet(FullViewStyles.get_tag_header_style())

    def set_tag_info(self, name: str, color: str = "#32CD32", count: int = 0):
        """
        Establecer información del tag

        Args:
            name: Nombre del tag de proyecto
            color: Color del tag en formato hex (por defecto: #32CD32)
            count: Cantidad de items en este tag (por defecto: 0)
        """
        self.tag_name = name
        self.tag_color = color
        self.item_count = count

        # Actualizar UI
        self.title_label.setText(f"// Tag: {name}")
        self.count_label.setText(f"({count} items)")

        # Aplicar color personalizado
        self.setStyleSheet(f"""
            ProjectTagHeaderWidget {{
                background-color: transparent;
                border-left: 3px solid {color};
                padding: 15px 15px 15px 20px;
                margin-top: 10px;
            }}
            QLabel#tag_title {{
                color: {color};
                font-size: 18px;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QLabel#tag_count {{
                color: #B0B0B0;
                font-size: 14px;
            }}
        """)

        # Actualizar color del botón de colapso
        self.collapse_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {color};
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: #7CFC00;
            }}
        """)

    def toggle_collapse(self):
        """
        Alternar estado de colapso

        Cambia entre estado colapsado y expandido,
        y emite la señal toggle_collapsed.
        """
        self.is_collapsed = not self.is_collapsed
        self.collapse_btn.setText("▶" if self.is_collapsed else "▼")
        self.toggle_collapsed.emit(self.is_collapsed)

    def set_collapsed(self, collapsed: bool):
        """
        Establecer estado de colapso

        Args:
            collapsed: True para colapsar, False para expandir
        """
        if self.is_collapsed != collapsed:
            self.toggle_collapse()

    def get_tag_name(self) -> str:
        """
        Obtener nombre del tag

        Returns:
            Nombre del tag
        """
        return self.tag_name

    def get_item_count(self) -> int:
        """
        Obtener cantidad de items

        Returns:
            Cantidad de items en este tag
        """
        return self.item_count

    def is_tag_collapsed(self) -> bool:
        """
        Verificar si el tag está colapsado

        Returns:
            True si está colapsado, False si está expandido
        """
        return self.is_collapsed

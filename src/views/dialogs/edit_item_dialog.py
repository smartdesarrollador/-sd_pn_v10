"""
Diálogo de Edición de Item

Ventana modal para editar items con todos sus campos y relaciones.
Maneja internamente las relaciones con:
- Lista (list_id)
- Tags de item (tags globales)
- Tags de proyecto/área (element tags)
- Proyecto/Área

Características:
- Campo Label (obligatorio)
- Campo Content (texto extenso con scroll)
- Selector múltiple de Tags globales
- Checkbox is_sensitive
- Validación de campos
- Actualización automática de relaciones

Autor: Widget Sidebar Team
Versión: 1.0
Fecha: 2025-12-26
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QCheckBox, QPushButton, QMessageBox, QScrollArea,
    QWidget, QFrame, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from src.views.widgets.item_tags_section import ItemTagsSection
from src.core.global_tag_manager import GlobalTagManager
import logging

logger = logging.getLogger(__name__)


class EditItemDialog(QDialog):
    """
    Diálogo modal para editar un item existente

    Permite editar:
    - Label (título del item)
    - Content (contenido del item)
    - Tags globales (selector múltiple)
    - is_sensitive (checkbox)

    Mantiene automáticamente las relaciones con:
    - Lista (list_id) - no se modifica
    - Proyecto/Área - no se modifica
    - Tags de elemento - se actualiza si se guardan cambios

    Señales:
        item_updated: Emitida cuando se guarda el item con éxito
    """

    # Señales
    item_updated = pyqtSignal(dict)  # Item actualizado

    def __init__(self, item_data: dict, db_manager, parent=None):
        """
        Inicializa el diálogo de edición

        Args:
            item_data: Diccionario con los datos completos del item
            db_manager: Instancia de DBManager
            parent: Widget padre
        """
        super().__init__(parent)
        self.db = db_manager
        self.item_data = item_data
        self.item_id = item_data.get('id')

        # Verificar que tengamos un ID válido
        if not self.item_id:
            raise ValueError("item_data debe contener un 'id' válido")

        # Configuración de ventana
        self.setWindowTitle(f"✏️ Editar Item - {item_data.get('label', 'Sin título')}")
        self.setMinimumSize(600, 700)
        self.setMaximumSize(800, 900)

        # Modal y siempre encima
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowTitleHint
        )

        self._setup_ui()
        self._load_data()
        self._apply_styles()

        logger.info(f"EditItemDialog inicializado para item ID {self.item_id}")

    def _setup_ui(self):
        """Configurar interfaz del diálogo"""
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título del diálogo
        title_label = QLabel("🖊️ Editar Item")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #00ff88; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #444;")
        layout.addWidget(separator)

        # Scroll area para el formulario
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #2d2d2d;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #555555;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #00ff88;
            }
        """)

        # Widget contenedor del formulario
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 10, 0)
        form_layout.setSpacing(15)

        # === CAMPO LABEL ===
        label_container = QWidget()
        label_layout = QVBoxLayout(label_container)
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.setSpacing(5)

        label_title = QLabel("📝 Label (Título) *")
        label_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        label_title.setStyleSheet("color: #ffffff;")
        label_layout.addWidget(label_title)

        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("Ej: Git status command, API Key, Ruta del proyecto...")
        self.label_input.setMinimumHeight(35)
        label_layout.addWidget(self.label_input)

        form_layout.addWidget(label_container)

        # === CAMPO TYPE ===
        type_container = QWidget()
        type_layout = QVBoxLayout(type_container)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setSpacing(5)

        type_title = QLabel("📦 Type (Tipo)")
        type_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        type_title.setStyleSheet("color: #ffffff;")
        type_layout.addWidget(type_title)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["TEXT", "CODE", "URL", "PATH"])
        self.type_combo.setMinimumHeight(35)
        self.type_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #444;
                border-radius: 6px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 10px;
            }
        """)
        type_layout.addWidget(self.type_combo)

        form_layout.addWidget(type_container)

        # === CAMPO CONTENT ===
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(5)

        content_title = QLabel("📄 Content (Contenido)")
        content_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        content_title.setStyleSheet("color: #ffffff;")
        content_layout.addWidget(content_title)

        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Ej: git status, https://api.example.com, C:\\Projects\\...")
        self.content_input.setMinimumHeight(200)
        self.content_input.setMaximumHeight(300)
        content_layout.addWidget(self.content_input)

        form_layout.addWidget(content_container)

        # === TAGS GLOBALES ===
        # Crear tag manager si tenemos db
        tag_manager = GlobalTagManager(self.db) if self.db else None

        # Widget de selector de tags
        self.tag_selector = ItemTagsSection(tag_manager=tag_manager)
        self.tag_selector.setMinimumHeight(200)
        self.tag_selector.setMaximumHeight(300)
        form_layout.addWidget(self.tag_selector)

        # === CHECKBOX IS_SENSITIVE ===
        self.sensitive_checkbox = QCheckBox("🔒 Marcar como sensible (cifrado)")
        self.sensitive_checkbox.setFont(QFont("Segoe UI", 10))
        self.sensitive_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #555;
                border-radius: 4px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:checked {
                background-color: #FF5722;
                border-color: #FF5722;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjMzMzMgNEw2IDExLjMzMzNMMi42NjY2NyA4IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
            QCheckBox::indicator:hover {
                border-color: #00ff88;
            }
        """)
        form_layout.addWidget(self.sensitive_checkbox)

        # Nota de advertencia para items sensibles
        self.sensitive_warning = QLabel(
            "⚠️ El contenido será cifrado. Necesitarás la contraseña maestra para acceder."
        )
        self.sensitive_warning.setWordWrap(True)
        self.sensitive_warning.setStyleSheet("""
            color: #FFA726;
            font-size: 9px;
            padding: 8px;
            background-color: rgba(255, 167, 38, 0.1);
            border-left: 3px solid #FFA726;
            border-radius: 4px;
        """)
        self.sensitive_warning.setVisible(False)
        form_layout.addWidget(self.sensitive_warning)

        # Conectar checkbox para mostrar/ocultar advertencia
        self.sensitive_checkbox.stateChanged.connect(
            lambda state: self.sensitive_warning.setVisible(state == Qt.CheckState.Checked.value)
        )

        # Spacer
        form_layout.addStretch()

        # Establecer widget en scroll area
        scroll_area.setWidget(form_widget)
        layout.addWidget(scroll_area, 1)

        # === BOTONES DE ACCIÓN ===
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 10, 0, 0)
        buttons_layout.setSpacing(10)

        # Información sobre relaciones
        info_label = QLabel("💡 Las relaciones con Lista/Proyecto/Área se mantienen automáticamente")
        info_label.setStyleSheet("color: #888; font-size: 9px;")
        info_label.setWordWrap(True)
        buttons_layout.addWidget(info_label)

        buttons_layout.addStretch()

        # Botón Cancelar
        cancel_btn = QPushButton("✕ Cancelar")
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: #ffffff;
                border: 1px solid #666;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #666;
                border-color: #777;
            }
            QPushButton:pressed {
                background-color: #444;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        # Botón Guardar
        self.save_btn = QPushButton("💾 Guardar Cambios")
        self.save_btn.setMinimumWidth(150)
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: #ffffff;
                border: 1px solid #45a049;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 700;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
                border-color: #3d8b40;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
                border-color: #444;
            }
        """)
        self.save_btn.clicked.connect(self._save_changes)
        buttons_layout.addWidget(self.save_btn)

        layout.addWidget(buttons_container)

    def _load_data(self):
        """Cargar datos del item en los campos del formulario"""
        try:
            # Cargar label
            self.label_input.setText(self.item_data.get('label', ''))

            # Cargar tipo
            current_type = self.item_data.get('type', 'TEXT')
            index = self.type_combo.findText(current_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)

            # Cargar content (descifrado si es sensible)
            content = self.item_data.get('content', '')
            self.content_input.setPlainText(content)

            # Cargar is_sensitive
            is_sensitive = self.item_data.get('is_sensitive', False)
            self.sensitive_checkbox.setChecked(bool(is_sensitive))

            # Cargar tags (si existen)
            tags = self.item_data.get('tags', [])
            logger.info(f"📋 Tags recibidos de item_data: {tags} (tipo: {type(tags)})")

            if tags:
                # Convertir lista de tags a lista de nombres
                tag_names = []
                if isinstance(tags, list) and len(tags) > 0:
                    logger.debug(f"   Primer tag (muestra): {tags[0]} (tipo: {type(tags[0])})")

                    if isinstance(tags[0], dict):
                        # Lista de dicts {'id': x, 'name': y}
                        tag_names = [tag['name'] for tag in tags if 'name' in tag]
                        logger.info(f"   Tags extraídos de dicts: {tag_names}")
                    else:
                        # Lista de strings
                        tag_names = tags
                        logger.info(f"   Tags ya son strings: {tag_names}")

                    if tag_names:
                        logger.info(f"🏷️  Estableciendo tags en selector: {tag_names}")
                        self.tag_selector.set_selected_tags(tag_names)
                        logger.info(f"✅ Tags cargados exitosamente")
                    else:
                        logger.warning(f"⚠️  tag_names está vacío después de conversión")
                else:
                    logger.warning(f"⚠️  tags no es una lista válida o está vacía")
            else:
                logger.info("ℹ️  Item sin tags")

            logger.info(f"Datos del item {self.item_id} cargados en el formulario")

        except Exception as e:
            logger.error(f"❌ Error cargando datos del item: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudieron cargar los datos del item:\n{str(e)}"
            )

    def _apply_styles(self):
        """Aplicar estilos CSS al diálogo"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit, QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #444;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #00ff88;
            }
            QLineEdit::placeholder, QTextEdit::placeholder {
                color: #666;
            }
        """)

    def _validate_input(self) -> bool:
        """
        Validar entrada del usuario

        Returns:
            True si todos los campos son válidos, False en caso contrario
        """
        # Validar label (obligatorio)
        label = self.label_input.text().strip()
        if not label:
            QMessageBox.warning(
                self,
                "Campo Requerido",
                "El campo 'Label' es obligatorio.\nPor favor ingresa un título para el item."
            )
            self.label_input.setFocus()
            return False

        # Content es opcional
        return True

    def _save_changes(self):
        """Guardar cambios del item"""
        # Validar entrada
        if not self._validate_input():
            return

        try:
            # Obtener valores del formulario
            new_label = self.label_input.text().strip()
            new_content = self.content_input.toPlainText().strip()
            new_type = self.type_combo.currentText()
            new_is_sensitive = self.sensitive_checkbox.isChecked()
            new_tags = self.tag_selector.get_selected_tags()

            # Preparar datos para actualizar
            update_data = {
                'label': new_label,
                'content': new_content,
                'type': new_type,
                'is_sensitive': new_is_sensitive,
                'tags': new_tags
            }

            # Actualizar item en BD
            self.db.update_item(self.item_id, **update_data)

            logger.info(f"✅ Item {self.item_id} actualizado: label='{new_label}', "
                       f"is_sensitive={new_is_sensitive}, tags={new_tags}")

            # Emitir señal con los datos actualizados
            updated_item_data = self.item_data.copy()
            updated_item_data.update({
                'label': new_label,
                'content': new_content,
                'type': new_type,
                'is_sensitive': new_is_sensitive,
                'tags': new_tags
            })
            self.item_updated.emit(updated_item_data)

            # Mostrar mensaje de éxito
            QMessageBox.information(
                self,
                "✅ Item Actualizado",
                f"El item '{new_label}' se actualizó correctamente."
            )

            # Cerrar diálogo
            self.accept()

        except Exception as e:
            logger.error(f"❌ Error guardando cambios del item: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudieron guardar los cambios:\n{str(e)}"
            )


# === TEST ===
if __name__ == '__main__':
    """Test del diálogo de edición"""
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Datos de prueba
    test_item_data = {
        'id': 1,
        'label': 'Test Item',
        'content': 'Este es el contenido de prueba',
        'type': 'TEXT',
        'is_sensitive': False,
        'tags': ['python', 'test', 'demo']
    }

    # Crear diálogo (sin DBManager para test)
    dialog = EditItemDialog(test_item_data, db_manager=None)
    dialog.show()

    sys.exit(app.exec())

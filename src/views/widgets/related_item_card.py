"""
Related Item Card Widget - Compact item display with checkbox for selection
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QCheckBox, QPushButton, QFrame, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QCursor
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.models.item import Item, ItemType
from styles.panel_styles import PanelStyles
from styles.futuristic_theme import get_theme

logger = logging.getLogger(__name__)


class RelatedItemCard(QFrame):
    """Widget compacto para mostrar un item con checkbox de selección"""

    # Señales
    checkbox_toggled = pyqtSignal(object, bool)  # item (Item object), is_checked
    copy_clicked = pyqtSignal(object)  # item (Item object)
    edit_requested = pyqtSignal(object)  # item (Item object)

    def __init__(self, item: Item, show_labels: bool = True, show_tags: bool = False,
                 show_content: bool = False, show_description: bool = False, parent=None):
        super().__init__(parent)

        self.item = item
        self.show_labels = show_labels
        self.show_tags = show_tags
        self.show_content = show_content
        self.show_description = show_description

        self.theme = get_theme()

        # State tracking
        self.is_selected_state = False
        self.is_revealed = False  # For sensitive content reveal

        self.init_ui()

    def init_ui(self):
        """Inicializar la interfaz del card"""
        # Frame properties - altura dinámica según opciones
        # Calcular altura necesaria - más compacto
        base_height = 36  # Altura base con solo label (reducida)
        if self.show_tags:
            base_height += 18
        if self.show_content:
            base_height += 18
        if self.show_description:
            base_height += 18

        self.setMinimumHeight(base_height)
        self.setMaximumHeight(base_height + 5)
        self.setMinimumWidth(300)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        # Apply enhanced item style with hover and selection states
        self.setStyleSheet(self._get_card_style())

        # Main horizontal layout - súper compacto
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 4, 8, 4)  # Márgenes mínimos
        main_layout.setSpacing(6)  # Espaciado mínimo

        # ========== CHECKBOX minimalista ==========
        self.checkbox = QCheckBox()
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
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
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        main_layout.addWidget(self.checkbox)

        # ========== TYPE ICON simple y minimalista ==========
        type_emoji = PanelStyles.get_icon_type_emoji(self.item.type)
        type_color = PanelStyles.get_icon_type_color(self.item.type)

        self.type_icon = QLabel(type_emoji)
        self.type_icon.setFixedSize(20, 20)
        self.type_icon.setStyleSheet(f"""
            QLabel {{
                color: {type_color};
                font-size: 14px;
                background: transparent;
                border: none;
                padding: 0px;
            }}
        """)
        self.type_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Tooltip mejorado
        tooltip_text = f"Tipo: {self.item.type}"
        if hasattr(self.item, 'created_at') and self.item.created_at:
            tooltip_text += f"\nCreado: {self.item.created_at}"
        if hasattr(self.item, 'usage_count') and self.item.usage_count:
            tooltip_text += f"\nUsos: {self.item.usage_count}"
        self.type_icon.setToolTip(tooltip_text)

        main_layout.addWidget(self.type_icon)

        # ========== ITEM INFO (horizontal cuando hay múltiples campos) ==========
        # Contar cuántos campos están visibles - convertir explícitamente a bool
        visible_fields = sum([
            bool(self.show_labels),
            bool(self.show_tags and hasattr(self.item, 'tags') and self.item.tags),
            bool(self.show_content and self.item.content),
            bool(self.show_description and self.item.description)
        ])

        # Si hay más de 1 campo visible, usar layout horizontal
        if visible_fields > 1:
            info_layout = QHBoxLayout()
            info_layout.setSpacing(8)
            info_layout.setContentsMargins(0, 0, 0, 0)
            use_horizontal = True
        else:
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)
            info_layout.setContentsMargins(0, 0, 0, 0)
            use_horizontal = False

        # Label (always shown if show_labels is True)
        if self.show_labels:
            # Truncar manualmente si es muy largo
            display_label = self.item.label
            max_length = 30 if use_horizontal else 50  # Más corto en horizontal
            if len(display_label) > max_length:
                display_label = display_label[:max_length] + "..."

            self.label_widget = QLabel(display_label)
            self.label_widget.setStyleSheet(f"""
                QLabel {{
                    color: {self.theme.get_color('text_primary')};
                    font-size: 10pt;
                    font-weight: bold;
                    background: transparent;
                    padding: 0px;
                    margin: 0px;
                }}
            """)
            self.label_widget.setWordWrap(False)
            self.label_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            if use_horizontal:
                self.label_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            else:
                self.label_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            # Tooltip siempre muestra el texto completo
            self.label_widget.setToolTip(f"{self.item.label}\nTipo: {self.item.type}")
            info_layout.addWidget(self.label_widget, 1 if use_horizontal else 0)

            # Agregar separador si estamos en horizontal y hay más campos
            if use_horizontal and visible_fields > 1:
                separator = QLabel("|")
                separator.setStyleSheet(f"""
                    QLabel {{
                        color: {self.theme.get_color('surface')};
                        font-size: 10pt;
                        padding: 0px 4px;
                    }}
                """)
                info_layout.addWidget(separator)

        # Tags (if enabled and item has tags)
        if self.show_tags and hasattr(self.item, 'tags') and self.item.tags:
            # Usar emoji de tag en horizontal
            if use_horizontal:
                tags_text = "🏷️ " + ", ".join(self.item.tags[:2])  # Máximo 2 tags
                if len(self.item.tags) > 2:
                    tags_text += f" +{len(self.item.tags) - 2}"
            else:
                tags_text = " ".join([f"#{tag}" for tag in self.item.tags])
                if len(tags_text) > 60:
                    tags_text = tags_text[:60] + "..."

            tags_label = QLabel(tags_text)
            tags_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.theme.get_color('warning')};
                    font-size: {'9pt' if use_horizontal else '8pt'};
                    background: transparent;
                }}
            """)
            tags_label.setWordWrap(False)
            tags_label.setSizePolicy(QSizePolicy.Policy.Preferred if use_horizontal else QSizePolicy.Policy.Expanding,
                                    QSizePolicy.Policy.Fixed)
            full_tags = " ".join([f"#{tag}" for tag in self.item.tags])
            tags_label.setToolTip(f"Tags: {full_tags}")
            info_layout.addWidget(tags_label, 0 if use_horizontal else 0)

            # Agregar separador si hay más campos después
            if use_horizontal and (self.show_content or self.show_description):
                separator = QLabel("|")
                separator.setStyleSheet(f"""
                    QLabel {{
                        color: {self.theme.get_color('surface')};
                        font-size: 10pt;
                        padding: 0px 4px;
                    }}
                """)
                info_layout.addWidget(separator)

        # Content preview (if enabled)
        if self.show_content and self.item.content:
            if self.item.is_sensitive:
                # Create horizontal layout for sensitive content with reveal button
                content_layout = QHBoxLayout()
                content_layout.setSpacing(5)
                content_layout.setContentsMargins(0, 0, 0, 0)

                self.content_label = QLabel("🔒 Contenido cifrado")
                self.content_label.setStyleSheet(f"""
                    QLabel {{
                        color: {self.theme.get_color('warning')};
                        font-size: 8pt;
                        background: transparent;
                    }}
                """)
                self.content_label.setWordWrap(False)
                content_layout.addWidget(self.content_label, 1)

                # Reveal button for sensitive content
                self.reveal_button = QPushButton("👁")
                self.reveal_button.setFixedSize(20, 20)
                self.reveal_button.setCursor(Qt.CursorShape.PointingHandCursor)
                self.reveal_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {self.theme.get_color('warning')};
                        border: 1px solid {self.theme.get_color('warning')};
                        border-radius: 3px;
                        font-size: 10pt;
                        padding: 0px;
                    }}
                    QPushButton:hover {{
                        background-color: {self.theme.get_color('warning')};
                        color: {self.theme.get_color('background_deep')};
                    }}
                """)
                self.reveal_button.setToolTip("Mostrar contenido sensible temporalmente")
                self.reveal_button.clicked.connect(self.toggle_reveal_sensitive)
                content_layout.addWidget(self.reveal_button)

                info_layout.addLayout(content_layout)
            else:
                # Truncar contenido según el modo
                max_content_len = 40 if use_horizontal else 80
                content_preview = self.item.content[:max_content_len]
                if len(self.item.content) > max_content_len:
                    content_preview += "..."

                # Agregar emoji de documento en horizontal
                if use_horizontal:
                    content_preview = "📄 " + content_preview

                self.content_label = QLabel(content_preview)
                self.content_label.setStyleSheet(f"""
                    QLabel {{
                        color: {self.theme.get_color('text_secondary')};
                        font-size: {'9pt' if use_horizontal else '8pt'};
                        background: transparent;
                    }}
                """)
                self.content_label.setWordWrap(False)
                self.content_label.setSizePolicy(QSizePolicy.Policy.Preferred if use_horizontal else QSizePolicy.Policy.Expanding,
                                                QSizePolicy.Policy.Fixed)
                self.content_label.setToolTip(f"Contenido:\n{self.item.content[:200]}")
                info_layout.addWidget(self.content_label, 0 if use_horizontal else 0)

        # Description (if enabled)
        if self.show_description and self.item.description:
            # Agregar separador si estamos en horizontal y no es el último campo
            if use_horizontal and self.show_content:
                separator = QLabel("|")
                separator.setStyleSheet(f"""
                    QLabel {{
                        color: {self.theme.get_color('surface')};
                        font-size: 10pt;
                        padding: 0px 4px;
                    }}
                """)
                info_layout.addWidget(separator)

            max_desc_len = 40 if use_horizontal else 100
            desc_text = self.item.description[:max_desc_len]
            if len(self.item.description) > max_desc_len:
                desc_text += "..."

            desc_label = QLabel(desc_text)
            desc_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.theme.get_color('text_secondary')};
                    font-size: {'9pt' if use_horizontal else '8pt'};
                    font-style: italic;
                    background: transparent;
                }}
            """)
            desc_label.setWordWrap(False)
            desc_label.setSizePolicy(QSizePolicy.Policy.Preferred if use_horizontal else QSizePolicy.Policy.Expanding,
                                    QSizePolicy.Policy.Fixed)
            desc_label.setToolTip(f"Descripción:\n{self.item.description}")
            info_layout.addWidget(desc_label, 0 if use_horizontal else 0)

        main_layout.addLayout(info_layout, 1)  # Stretch factor 1

        # ========== BADGES ==========
        # Favorite badge
        if hasattr(self.item, 'is_favorite') and self.item.is_favorite:
            fav_badge = QLabel("⭐")
            fav_badge.setStyleSheet(PanelStyles.get_badge_style('favorite'))
            fav_badge.setToolTip("Favorito")
            main_layout.addWidget(fav_badge)

        # Sensitive badge
        if self.item.is_sensitive:
            sensitive_badge = QLabel("🔒")
            sensitive_badge.setStyleSheet(PanelStyles.get_badge_style('default'))
            sensitive_badge.setToolTip("Contenido sensible")
            main_layout.addWidget(sensitive_badge)

        # ========== COPY BUTTON minimalista ==========
        self.copy_button = QPushButton("📋")
        self.copy_button.setFixedSize(24, 24)
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme.get_color('text_primary')};
                border: none;
                border-radius: 0px;
                font-size: 11pt;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {self.theme.get_color('surface')};
            }}
            QPushButton:pressed {{
                background-color: {self.theme.get_color('accent')};
            }}
        """)
        self.copy_button.setToolTip("Copiar al portapapeles")
        self.copy_button.clicked.connect(self.on_copy_clicked)
        main_layout.addWidget(self.copy_button)

        # Set tooltip
        self._update_tooltip()

    def _hex_to_rgba(self, hex_color: str, alpha: float = 1.0) -> str:
        """Convertir color hex a rgba"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"({r}, {g}, {b}, {alpha})"
        return "(50, 50, 50, 0.1)"  # Fallback

    def _update_tooltip(self):
        """Actualizar tooltip del card"""
        tooltip_parts = []

        if self.item.description:
            tooltip_parts.append(self.item.description)

        if not self.item.is_sensitive and self.item.content:
            preview = self.item.content[:100]
            if len(self.item.content) > 100:
                preview += "..."
            tooltip_parts.append(f"\n{preview}")

        tooltip_parts.append(f"\nTipo: {self.item.type}")

        self.setToolTip("\n".join(tooltip_parts))

    def on_checkbox_changed(self, state):
        """Handle checkbox state change"""
        is_checked = state == Qt.CheckState.Checked.value
        self.is_selected_state = is_checked

        # Update card appearance based on selection
        self.setStyleSheet(self._get_card_style())

        self.checkbox_toggled.emit(self.item, is_checked)

    def on_copy_clicked(self):
        """Handle copy button click"""
        # Copy to clipboard
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.item.content)

        logger.info(f"Item copied to clipboard: {self.item.label}")

        # Visual feedback
        original_text = self.copy_button.text()
        self.copy_button.setText("✅")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1000, lambda: self.copy_button.setText(original_text))

        # Emit signal
        self.copy_clicked.emit(self.item)

    def set_checked(self, checked: bool):
        """Establecer el estado del checkbox programáticamente"""
        self.checkbox.setChecked(checked)

    def is_checked(self) -> bool:
        """Obtener el estado actual del checkbox"""
        return self.checkbox.isChecked()

    def toggle_reveal_sensitive(self):
        """Toggle reveal of sensitive content (temporary, auto-hide after 5 seconds)"""
        # Check if widget still exists
        try:
            if not self.isVisible():
                return
        except RuntimeError:
            # Widget has been deleted
            return

        if not self.item.is_sensitive or not self.show_content:
            return

        if self.is_revealed:
            # Hide content again
            self.content_label.setText("🔒 Contenido cifrado")
            self.content_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.theme.get_color('warning')};
                    font-size: 8pt;
                    background: transparent;
                }}
            """)
            self.reveal_button.setText("👁")
            self.is_revealed = False
            logger.info("Sensitive content hidden")
        else:
            # Show content
            content_preview = self.item.content[:80]
            if len(self.item.content) > 80:
                content_preview += "..."

            self.content_label.setText(content_preview)
            self.content_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.theme.get_color('success')};
                    font-size: 8pt;
                    background: transparent;
                    font-weight: bold;
                }}
            """)
            self.reveal_button.setText("🙈")
            self.is_revealed = True
            logger.info("Sensitive content revealed")

            # Auto-hide after 5 seconds
            QTimer.singleShot(5000, self.toggle_reveal_sensitive)

    def _get_card_style(self) -> str:
        """Obtener estilos del card según estado (normal, hover, seleccionado)"""
        base_bg = self.theme.get_color('background_mid')
        hover_bg = self.theme.get_color('surface')
        selected_bg = self.theme.get_color('primary_dark') if hasattr(self.theme, 'get_color') else '#1e3a5f'

        # Si está seleccionado, usar color de selección
        if self.is_selected_state:
            bg_color = selected_bg
        else:
            bg_color = base_bg

        return f"""
            RelatedItemCard {{
                background-color: {bg_color};
                border: none;
                border-radius: 0px;
                margin: 1px 0px;
            }}
            RelatedItemCard:hover {{
                background-color: {hover_bg};
            }}
        """

    def enterEvent(self, event):
        """Handle mouse enter event for hover effect"""
        try:
            super().enterEvent(event)
            if not self.is_selected_state:
                # Apply hover style
                self.setProperty("hover", True)
                self.style().unpolish(self)
                self.style().polish(self)
        except RuntimeError:
            # Widget ya fue eliminado - ignorar silenciosamente
            pass

    def leaveEvent(self, event):
        """Handle mouse leave event"""
        try:
            super().leaveEvent(event)
            if not self.is_selected_state:
                # Remove hover style
                self.setProperty("hover", False)
                self.style().unpolish(self)
                self.style().polish(self)
        except RuntimeError:
            # Widget ya fue eliminado - ignorar silenciosamente
            pass

    def mouseDoubleClickEvent(self, event):
        """Handle double click to edit item"""
        if event.button() == Qt.MouseButton.LeftButton:
            logger.info(f"Double click on item: {self.item.label}")
            self.edit_requested.emit(self.item)
        super().mouseDoubleClickEvent(event)

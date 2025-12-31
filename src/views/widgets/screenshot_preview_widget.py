# -*- coding: utf-8 -*-
"""
Widget de vista previa de captura de pantalla para Creador Masivo

Muestra:
- Miniatura de la imagen (100x100px)
- Campo de texto editable para el label
- Botón de eliminar
- Información del archivo (dimensiones, tamaño)

Autor: Widget Sidebar Team
Versión: 1.0
Fecha: 2025-12-30
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QFont
from pathlib import Path
import os


class ScreenshotPreviewWidget(QFrame):
    """
    Widget de vista previa de captura

    Señales:
        remove_requested: Usuario quiere eliminar esta captura
        label_changed(str): Usuario cambió el label
    """

    # Señales
    remove_requested = pyqtSignal()
    label_changed = pyqtSignal(str)  # new_label

    def __init__(self, image_path: str, label: str = "", parent=None):
        """
        Inicializar widget de preview

        Args:
            image_path: Ruta completa a la imagen
            label: Label inicial de la captura
            parent: Widget padre
        """
        super().__init__(parent)

        self.image_path = image_path
        self._label = label

        self._setup_ui()
        self._apply_styles()
        self._load_image()
        self._load_metadata()

    def _setup_ui(self):
        """Configurar interfaz del widget"""
        # Frame con borde
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)

        # Layout principal horizontal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Miniatura (izquierda)
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(100, 100)
        self.thumbnail_label.setScaledContents(False)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 2px solid #555;
                border-radius: 4px;
                background-color: #2d2d2d;
            }
        """)
        layout.addWidget(self.thumbnail_label)

        # Contenedor de información (centro)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        # Label editable
        label_layout = QHBoxLayout()
        label_layout.setSpacing(5)

        label_title = QLabel("Label:")
        label_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        label_layout.addWidget(label_title)

        self.label_input = QLineEdit()
        self.label_input.setText(self._label)
        self.label_input.setPlaceholderText("Nombre de la captura...")
        self.label_input.textChanged.connect(self._on_label_changed)
        label_layout.addWidget(self.label_input)

        info_layout.addLayout(label_layout)

        # Nombre de archivo
        self.filename_label = QLabel(os.path.basename(self.image_path))
        self.filename_label.setFont(QFont("Segoe UI", 8))
        self.filename_label.setStyleSheet("color: #888;")
        info_layout.addWidget(self.filename_label)

        # Metadatos (dimensiones, tamaño)
        self.metadata_label = QLabel("Cargando...")
        self.metadata_label.setFont(QFont("Segoe UI", 8))
        self.metadata_label.setStyleSheet("color: #888;")
        info_layout.addWidget(self.metadata_label)

        info_layout.addStretch()

        layout.addLayout(info_layout)

        # Botón de eliminar (derecha)
        self.remove_btn = QPushButton("🗑️")
        self.remove_btn.setFixedSize(30, 30)
        self.remove_btn.setToolTip("Eliminar captura")
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        layout.addWidget(self.remove_btn, alignment=Qt.AlignmentFlag.AlignTop)

    def _apply_styles(self):
        """Aplicar estilos CSS"""
        self.setStyleSheet("""
            ScreenshotPreviewWidget {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 6px;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
            QPushButton:pressed {
                background-color: #7f0000;
            }
        """)

    def _load_image(self):
        """Cargar imagen y crear miniatura"""
        if not os.path.exists(self.image_path):
            self.thumbnail_label.setText("❌\nNo encontrada")
            return

        try:
            # Cargar imagen
            pixmap = QPixmap(self.image_path)

            if pixmap.isNull():
                self.thumbnail_label.setText("❌\nError carga")
                return

            # Escalar manteniendo aspect ratio
            scaled_pixmap = pixmap.scaled(
                100, 100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.thumbnail_label.setPixmap(scaled_pixmap)

        except Exception as e:
            self.thumbnail_label.setText(f"❌\n{str(e)[:20]}")

    def _load_metadata(self):
        """Cargar metadatos de la imagen"""
        if not os.path.exists(self.image_path):
            self.metadata_label.setText("Archivo no encontrado")
            return

        try:
            # Obtener dimensiones
            pixmap = QPixmap(self.image_path)
            width = pixmap.width()
            height = pixmap.height()

            # Obtener tamaño de archivo
            file_size = os.path.getsize(self.image_path)
            size_kb = file_size / 1024

            # Formatear
            if size_kb < 1024:
                size_str = f"{size_kb:.0f}KB"
            else:
                size_mb = size_kb / 1024
                size_str = f"{size_mb:.1f}MB"

            metadata_text = f"{width}×{height} • {size_str}"
            self.metadata_label.setText(metadata_text)

        except Exception as e:
            self.metadata_label.setText("Error leyendo metadatos")

    def _on_label_changed(self, new_text: str):
        """Callback cuando cambia el label"""
        self._label = new_text
        self.label_changed.emit(new_text)

    def _on_remove_clicked(self):
        """Callback cuando se hace clic en eliminar"""
        self.remove_requested.emit()

    def get_label(self) -> str:
        """Obtener label actual"""
        return self._label

    def get_filepath(self) -> str:
        """Obtener ruta completa de la imagen"""
        return self.image_path

    def get_filename(self) -> str:
        """Obtener solo nombre de archivo"""
        return os.path.basename(self.image_path)

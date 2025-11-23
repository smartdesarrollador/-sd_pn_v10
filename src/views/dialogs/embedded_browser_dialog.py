"""
Embedded Browser Dialog para renderización segura de items WEB_STATIC.

Este diálogo proporciona un navegador embebido con sandboxing completo
para visualizar aplicaciones web estáticas de forma segura.
"""

import sys
from pathlib import Path
import logging

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.html_validator import sanitize_html_for_rendering

logger = logging.getLogger(__name__)


class EmbeddedBrowserDialog(QDialog):
    """
    Diálogo con navegador embebido para renderizar items WEB_STATIC.

    Características de seguridad:
    - Sandboxing completo (sin acceso a archivos locales ni red)
    - Content Security Policy inyectado automáticamente
    - localStorage deshabilitado
    - JavaScript habilitado pero aislado
    """

    def __init__(self, url=None, html_content=None, parent=None):
        """
        Inicializa el diálogo del navegador embebido.

        Args:
            url: URL a cargar (modo navegador normal) - opcional
            html_content: HTML estático a renderizar (modo WEB_STATIC) - opcional
            parent: Widget padre
        """
        super().__init__(parent)

        self.url = url
        self.html_content = html_content

        self.setWindowTitle("Renderizador Web Estático")
        self.setModal(False)
        self.resize(1000, 700)

        self._init_ui()

        # Si es HTML estático, configurar sandboxing
        if html_content:
            self._setup_sandboxing()

        logger.info(f"EmbeddedBrowserDialog initialized (html_content={bool(html_content)}, url={bool(url)})")

    def _init_ui(self):
        """Inicializa la interfaz del diálogo"""
        # Aplicar tema oscuro
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #00d4ff;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header con indicador de modo seguro
        if self.html_content:
            header_widget = self._create_security_header()
            layout.addWidget(header_widget)

        # Navegador embebido
        self.browser = QWebEngineView()
        layout.addWidget(self.browser)

        # Footer con botón de cerrar
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(10, 10, 10, 10)

        footer_layout.addStretch()

        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.close)
        close_btn.setMinimumWidth(100)
        footer_layout.addWidget(close_btn)

        layout.addLayout(footer_layout)

    def _create_security_header(self):
        """Crea header con indicadores de seguridad"""
        from PyQt6.QtWidgets import QWidget

        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-bottom: 2px solid #4CAF50;
            }
        """)
        header.setFixedHeight(50)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 10, 15, 10)

        # Ícono de seguridad
        security_icon = QLabel("🔒")
        security_icon.setStyleSheet("font-size: 20pt;")
        header_layout.addWidget(security_icon)

        # Texto de seguridad
        security_label = QLabel("Modo Seguro Activo")
        security_label.setStyleSheet("font-weight: bold; font-size: 11pt; color: #4CAF50;")
        header_layout.addWidget(security_label)

        # Descripción
        desc_label = QLabel("• Sin acceso a red  • Sin acceso a archivos  • localStorage deshabilitado")
        desc_label.setStyleSheet("color: #888888; font-size: 9pt;")
        header_layout.addWidget(desc_label)

        header_layout.addStretch()

        return header

    def _setup_sandboxing(self):
        """
        Configura sandboxing de seguridad para contenido WEB_STATIC.

        Implementa 3 capas de seguridad:
        1. QWebEngineSettings: Deshabilita características peligrosas
        2. CSP: Inyectado automáticamente en HTML
        3. Aislamiento: Sin acceso a red, archivos o almacenamiento
        """
        settings = self.browser.settings()

        # === CAPA 1: QWebEngineSettings Sandboxing ===

        # Deshabilitar almacenamiento local
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, False)

        # Deshabilitar acceso a archivos locales desde contenido local
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, False)

        # Deshabilitar acceso a URLs remotas desde contenido local
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)

        # Deshabilitar contenido inseguro
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, False)

        # JavaScript habilitado pero sandboxed (necesario para calculadoras/apps)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        # Deshabilitar plugins (Flash, Java, etc.)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)

        # Deshabilitar geolocalización
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)

        # Deshabilitar acceso a clipboard desde JavaScript (si está disponible)
        # settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, False)

        logger.info("Sandboxing de seguridad configurado para WEB_STATIC:")
        logger.info("  - LocalStorage: DESHABILITADO")
        logger.info("  - Acceso a archivos locales: BLOQUEADO")
        logger.info("  - Acceso a URLs remotas: BLOQUEADO")
        logger.info("  - Contenido inseguro: BLOQUEADO")
        logger.info("  - JavaScript: HABILITADO (pero sandboxed)")
        logger.info("  - Plugins: DESHABILITADO")

    def load_static_html(self, html_content: str):
        """
        Carga HTML estático con sanitización y CSP.

        Args:
            html_content: HTML crudo del item WEB_STATIC
        """
        # === CAPA 2: Sanitización e inyección de CSP ===
        sanitized_html = sanitize_html_for_rendering(html_content)

        # Cargar en navegador con baseUrl vacía (sin acceso a recursos externos)
        self.browser.setHtml(sanitized_html, QUrl())

        size_kb = len(html_content) / 1024
        sanitized_size_kb = len(sanitized_html) / 1024

        logger.info(f"HTML estático cargado:")
        logger.info(f"  - Tamaño original: {size_kb:.1f} KB")
        logger.info(f"  - Tamaño sanitizado: {sanitized_size_kb:.1f} KB")
        logger.info(f"  - CSP inyectado: SÍ")

    def load_url(self, url: str):
        """
        Carga una URL en el navegador (modo normal, sin sandboxing).

        Args:
            url: URL a cargar
        """
        logger.info(f"Loading URL: {url}")
        self.browser.setUrl(QUrl(url))

    def showEvent(self, event):
        """Override: cargar HTML al mostrar si es contenido estático"""
        super().showEvent(event)

        if self.html_content:
            # Modo WEB_STATIC: cargar HTML sanitizado
            self.load_static_html(self.html_content)
        elif self.url:
            # Modo URL normal: cargar URL
            self.load_url(self.url)
        else:
            logger.warning("EmbeddedBrowserDialog mostrado sin contenido HTML ni URL")

    def get_browser_console_messages(self):
        """
        Obtiene mensajes de consola del navegador para debugging.

        Nota: Requiere conectar señal javaScriptConsoleMessage
        """
        # Esta funcionalidad requiere sobrescribir QWebEnginePage
        # Por ahora es placeholder para futura implementación
        pass

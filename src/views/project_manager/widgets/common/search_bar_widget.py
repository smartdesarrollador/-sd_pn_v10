"""
Widget de búsqueda tipo Ctrl+F para vista completa de proyectos

Proporciona búsqueda en tiempo real con navegación entre resultados
y resaltado de texto similar al Ctrl+F de navegadores.

Autor: Widget Sidebar Team
Versión: 1.0
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QKeyEvent


class SearchBarWidget(QWidget):
    """
    Barra de búsqueda tipo Ctrl+F

    Características:
    - Campo de texto con búsqueda en tiempo real (debounce 300ms)
    - Botones de navegación (anterior/siguiente)
    - Contador de resultados (ej: "2 de 15")
    - Botón cerrar
    - Atajo Esc para cerrar

    Señales:
        search_text_changed: Emitida cuando cambia el texto de búsqueda
        next_result: Emitida cuando se presiona botón siguiente
        previous_result: Emitida cuando se presiona botón anterior
        search_closed: Emitida cuando se cierra la búsqueda
    """

    # Señales
    search_text_changed = pyqtSignal(str)  # Texto de búsqueda
    next_result = pyqtSignal()  # Ir al siguiente resultado
    previous_result = pyqtSignal()  # Ir al resultado anterior
    search_closed = pyqtSignal()  # Cerrar búsqueda

    def __init__(self, parent=None):
        """
        Inicializar widget de búsqueda

        Args:
            parent: Widget padre
        """
        super().__init__(parent)

        # Estado interno
        self.current_index = 0
        self.total_results = 0
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._emit_search_changed)

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """Inicializar interfaz de usuario"""
        # Layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)

        # Campo de búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar en vista completa...")
        self.search_input.setFixedHeight(30)
        self.search_input.setMinimumWidth(200)  # Reducido 20% (250 → 200)
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.returnPressed.connect(self.next_result.emit)
        layout.addWidget(self.search_input)

        # Contador de resultados
        self.result_counter = QLabel("0 de 0")
        self.result_counter.setFixedWidth(70)
        self.result_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_counter)

        # Botón anterior
        self.prev_btn = QPushButton("◄")
        self.prev_btn.setFixedSize(30, 30)
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.clicked.connect(self.previous_result.emit)
        self.prev_btn.setToolTip("Resultado anterior (Shift+Enter)")
        layout.addWidget(self.prev_btn)

        # Botón siguiente
        self.next_btn = QPushButton("►")
        self.next_btn.setFixedSize(30, 30)
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.clicked.connect(self.next_result.emit)
        self.next_btn.setToolTip("Siguiente resultado (Enter)")
        layout.addWidget(self.next_btn)

        # Botón cerrar
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self._on_close)
        self.close_btn.setToolTip("Cerrar búsqueda (Esc)")
        layout.addWidget(self.close_btn)

        # Deshabilitar botones inicialmente
        self.update_navigation_state(False)

    def apply_styles(self):
        """Aplicar estilos CSS al widget"""
        self.setStyleSheet("""
            QWidget {
                background-color: #2C2C2C;
                border-bottom: 1px solid #404040;
            }

            QLineEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }

            QLineEdit:focus {
                border-color: #32CD32;
                background-color: #252525;
            }

            QLabel {
                color: #808080;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }

            QPushButton {
                background-color: #3C3C3C;
                color: #E0E0E0;
                border: 1px solid #505050;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #4C4C4C;
                border-color: #32CD32;
                color: #32CD32;
            }

            QPushButton:pressed {
                background-color: #2C2C2C;
            }

            QPushButton:disabled {
                background-color: #2C2C2C;
                color: #505050;
                border-color: #3C3C3C;
            }
        """)

    def _on_text_changed(self, text: str):
        """
        Manejar cambio de texto con debounce

        Args:
            text: Texto ingresado
        """
        # Reiniciar timer de debounce
        self.search_timer.stop()

        if text:
            # Esperar 300ms antes de buscar
            self.search_timer.start(300)
        else:
            # Si el texto está vacío, emitir inmediatamente
            self._emit_search_changed()

    def _emit_search_changed(self):
        """Emitir señal de búsqueda cambiada"""
        text = self.search_input.text()
        self.search_text_changed.emit(text)

    def _on_close(self):
        """Cerrar búsqueda"""
        self.search_input.clear()
        self.search_closed.emit()

    def update_results(self, current: int, total: int):
        """
        Actualizar contador de resultados

        Args:
            current: Índice del resultado actual (0-based)
            total: Total de resultados encontrados
        """
        self.current_index = current
        self.total_results = total

        if total > 0:
            # Mostrar contador (convertir a 1-based para el usuario)
            self.result_counter.setText(f"{current + 1} de {total}")
            self.result_counter.setStyleSheet("color: #32CD32; font-weight: bold;")
            self.update_navigation_state(True)
        else:
            # No hay resultados
            if self.search_input.text():
                self.result_counter.setText("0 resultados")
                self.result_counter.setStyleSheet("color: #FF6B6B; font-weight: bold;")
            else:
                self.result_counter.setText("0 de 0")
                self.result_counter.setStyleSheet("color: #808080;")
            self.update_navigation_state(False)

    def update_navigation_state(self, enabled: bool):
        """
        Habilitar/deshabilitar botones de navegación

        Args:
            enabled: True para habilitar, False para deshabilitar
        """
        self.prev_btn.setEnabled(enabled)
        self.next_btn.setEnabled(enabled)

    def focus_search_input(self):
        """Dar foco al campo de búsqueda"""
        self.search_input.setFocus()
        self.search_input.selectAll()

    def get_search_text(self) -> str:
        """
        Obtener texto de búsqueda actual

        Returns:
            Texto de búsqueda
        """
        return self.search_input.text()

    def clear_search(self):
        """Limpiar búsqueda"""
        self.search_input.clear()
        self.update_results(0, 0)

    def keyPressEvent(self, event: QKeyEvent):
        """
        Manejar eventos de teclado

        Args:
            event: Evento de teclado
        """
        if event.key() == Qt.Key.Key_Escape:
            self._on_close()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                self.previous_result.emit()
            else:
                self.next_result.emit()
        else:
            super().keyPressEvent(event)


# Test del widget (para desarrollo)
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QVBoxLayout

    app = QApplication(sys.argv)

    # Crear ventana de prueba
    window = QWidget()
    window.setWindowTitle("SearchBarWidget - Test")
    window.setMinimumSize(600, 100)

    layout = QVBoxLayout(window)

    # Crear widget de búsqueda
    search_bar = SearchBarWidget()

    # Conectar señales para testing
    search_bar.search_text_changed.connect(
        lambda text: print(f"Búsqueda: '{text}'")
    )
    search_bar.next_result.connect(
        lambda: print("Siguiente resultado")
    )
    search_bar.previous_result.connect(
        lambda: print("Resultado anterior")
    )
    search_bar.search_closed.connect(
        lambda: print("Búsqueda cerrada")
    )

    layout.addWidget(search_bar)
    layout.addStretch()

    # Simular resultados después de 2 segundos
    def simulate_results():
        search_bar.update_results(0, 5)

    QTimer.singleShot(2000, simulate_results)

    window.show()
    sys.exit(app.exec())

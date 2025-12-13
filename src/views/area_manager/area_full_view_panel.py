from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from ..project_manager.styles.full_view_styles import FullViewStyles
from ..project_manager.widgets.headers import ProjectHeaderWidget, ProjectTagHeaderWidget
from ..project_manager.widgets.item_group_widget import ItemGroupWidget
from .area_data_manager import AreaDataManager


class AreaFullViewPanel(QWidget):
    item_copied = pyqtSignal(dict)
    item_clicked = pyqtSignal(dict)

    def __init__(self, db_manager=None, parent=None):
        super().__init__(parent)

        self.data_manager = AreaDataManager(db_manager)
        self.area_data = None
        self.current_filters = []
        self.current_area_id = None

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

        self.show_empty_state()

    def apply_styles(self):
        self.setStyleSheet(FullViewStyles.get_main_panel_style())

    def show_empty_state(self):
        self.clear_view()

        empty_label = QLabel("Selecciona un área para ver su contenido")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet(f"""
            color: #808080;
            font-size: 14px;
            padding: 50px;
            font-family: 'Segoe UI', Arial, sans-serif;
        """)

        self.content_layout.addWidget(empty_label)

    def load_area(self, area_id: int):
        self.current_area_id = area_id
        self.area_data = self.data_manager.get_area_full_data(area_id)

        if not self.area_data:
            self.show_empty_state()
            return

        self.render_view()

    def render_view(self):
        if not self.area_data:
            return

        self.clear_view()

        area_header = ProjectHeaderWidget()
        area_header.set_project_info(
            self.area_data['area_name'],
            self.area_data['area_icon']
        )
        self.content_layout.addWidget(area_header)

        for tag_data in self.area_data['tags']:
            self._render_tag_section(tag_data)

        if self.area_data.get('unclassified_elements'):
            self._render_unclassified_section(self.area_data['unclassified_elements'])

        if self.area_data['ungrouped_items']:
            self._render_ungrouped_section(self.area_data['ungrouped_items'])

        self.content_layout.addStretch()

    def _render_tag_section(self, tag_data: dict):
        total_items = sum(
            len(group['items'])
            for group in tag_data['groups']
        )

        tag_header = ProjectTagHeaderWidget()
        tag_header.set_tag_info(
            tag_data['tag_name'],
            tag_data['tag_color'],
            total_items
        )
        self.content_layout.addWidget(tag_header)

        tag_container = QWidget()
        tag_container_layout = QVBoxLayout(tag_container)
        tag_container_layout.setContentsMargins(0, 0, 0, 0)
        tag_container_layout.setSpacing(8)

        for group in tag_data['groups']:
            group_widget = ItemGroupWidget(
                group['name'],
                group['type']
            )

            for item_data in group['items']:
                group_widget.add_item(item_data)

            tag_container_layout.addWidget(group_widget)

        self.content_layout.addWidget(tag_container)

        tag_header.toggle_collapsed.connect(
            lambda collapsed: tag_container.setVisible(not collapsed)
        )

    def _render_unclassified_section(self, elements: list):
        tag_header = ProjectTagHeaderWidget()
        total_items = sum(len(elem['items']) for elem in elements)
        tag_header.set_tag_info("Sin Clasificar", "#808080", total_items)
        self.content_layout.addWidget(tag_header)

        tag_container = QWidget()
        tag_container_layout = QVBoxLayout(tag_container)
        tag_container_layout.setContentsMargins(0, 0, 0, 0)
        tag_container_layout.setSpacing(8)

        for elem in elements:
            group_widget = ItemGroupWidget(elem['name'], elem['type'])
            for item_data in elem['items']:
                group_widget.add_item(item_data)
            tag_container_layout.addWidget(group_widget)

        self.content_layout.addWidget(tag_container)

        tag_header.toggle_collapsed.connect(
            lambda collapsed: tag_container.setVisible(not collapsed)
        )

    def _render_ungrouped_section(self, items: list):
        tag_header = ProjectTagHeaderWidget()
        tag_header.set_tag_info("Otros Items", "#808080", len(items))
        self.content_layout.addWidget(tag_header)

        group_widget = ItemGroupWidget("Sin clasificar", "other")
        for item_data in items:
            group_widget.add_item(item_data)

        self.content_layout.addWidget(group_widget)

    def apply_filters(self, tag_filters: list[str], match_mode: str = 'OR'):
        self.current_filters = tag_filters

        if not self.area_data:
            return

        if not tag_filters:
            self.render_view()
            return

        filtered_data = self.data_manager.filter_by_area_tags(
            self.area_data,
            tag_filters,
            match_mode
        )

        original_data = self.area_data
        self.area_data = filtered_data
        self.render_view()
        self.area_data = original_data

        visible_tags = [tag['tag_name'] for tag in filtered_data['tags']]
        print(f"✓ Filtros aplicados ({match_mode}): {tag_filters}")
        print(f"  Tags visibles: {visible_tags}")

    def clear_filters(self):
        self.current_filters = []
        if self.area_data:
            self.render_view()
            print("✓ Filtros limpiados - Mostrando todos los tags")

    def refresh_view(self):
        if self.current_area_id:
            self.load_area(self.current_area_id)

    def clear_view(self):
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def get_current_area_id(self) -> int:
        return self.current_area_id

    def has_active_filters(self) -> bool:
        return len(self.current_filters) > 0

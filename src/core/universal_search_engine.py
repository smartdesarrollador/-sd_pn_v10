"""
Universal Search Engine for Widget Sidebar
Coordina búsquedas globales de items y tags mostrando todas sus relaciones
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from enum import Enum

logger = logging.getLogger(__name__)


class SearchResultType(Enum):
    """Tipos de resultados de búsqueda"""
    ITEM = "item"
    TAG = "tag"
    CATEGORY_TAG = "category_tag"
    PROJECT_TAG = "project_tag"
    AREA_TAG = "area_tag"


class EntityType(Enum):
    """Tipos de entidades que pueden contener items/tags"""
    PROYECTO = "proyecto"
    AREA = "area"
    CATEGORIA = "categoria"
    TABLA = "tabla"
    PROCESO = "proceso"
    LISTA = "lista"


@dataclass
class ItemRelationships:
    """Estructura de datos para relaciones de un item"""
    proyectos: List[str] = field(default_factory=list)
    areas: List[str] = field(default_factory=list)
    categoria: Optional[str] = None
    tabla: Optional[str] = None
    procesos: List[str] = field(default_factory=list)
    lista: Optional[str] = None

    def has_any_relationship(self) -> bool:
        """Verifica si el item tiene alguna relación"""
        return bool(
            self.proyectos or self.areas or self.categoria or
            self.tabla or self.procesos or self.lista
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización"""
        return {
            'proyectos': self.proyectos,
            'areas': self.areas,
            'categoria': self.categoria,
            'tabla': self.tabla,
            'procesos': self.procesos,
            'lista': self.lista
        }


@dataclass
class SearchResult:
    """Resultado de búsqueda universal"""
    result_type: SearchResultType
    id: int
    name: str
    content: str = ""  # Para items
    icon: str = ""
    color: str = ""
    description: str = ""

    # Relaciones - pueden ser múltiples
    proyectos: List[str] = field(default_factory=list)
    areas: List[str] = field(default_factory=list)
    categoria: Optional[str] = None
    tabla: Optional[str] = None
    procesos: List[str] = field(default_factory=list)
    lista: Optional[str] = None

    # Tags asociados
    tags: List[str] = field(default_factory=list)

    # Metadata adicional
    use_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    last_used: str = ""
    is_sensitive: bool = False
    is_favorite: bool = False

    def matches_entity_filter(self, entity_filters: Dict[str, bool]) -> bool:
        """
        Verifica si el resultado coincide con los filtros de entidad activos

        Args:
            entity_filters: Dict con keys 'proyectos', 'areas', 'categorias', 'tablas', 'procesos'
                           y valores booleanos indicando si el filtro está activo

        Returns:
            True si el resultado debe mostrarse según los filtros
        """
        # Si no hay filtros activos, mostrar todo
        if not any(entity_filters.values()):
            return True

        # Verificar cada tipo de entidad
        has_match = False

        if entity_filters.get('proyectos', False) and self.proyectos:
            has_match = True
        if entity_filters.get('areas', False) and self.areas:
            has_match = True
        if entity_filters.get('categorias', False) and self.categoria:
            has_match = True
        if entity_filters.get('tablas', False) and self.tabla:
            has_match = True
        if entity_filters.get('procesos', False) and self.procesos:
            has_match = True

        return has_match

    def has_all_tags(self, required_tags: List[str]) -> bool:
        """
        Verifica si el resultado tiene todos los tags requeridos (lógica AND)

        Args:
            required_tags: Lista de tags que debe tener el resultado

        Returns:
            True si tiene todos los tags requeridos
        """
        if not required_tags:
            return True

        result_tags_lower = {tag.lower() for tag in self.tags}
        return all(tag.lower() in result_tags_lower for tag in required_tags)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización"""
        return {
            'result_type': self.result_type.value,
            'id': self.id,
            'name': self.name,
            'content': self.content,
            'icon': self.icon,
            'color': self.color,
            'description': self.description,
            'proyectos': self.proyectos,
            'areas': self.areas,
            'categoria': self.categoria,
            'tabla': self.tabla,
            'procesos': self.procesos,
            'lista': self.lista,
            'tags': self.tags,
            'use_count': self.use_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_used': self.last_used,
            'is_sensitive': self.is_sensitive,
            'is_favorite': self.is_favorite
        }


class UniversalSearchEngine:
    """
    Motor de búsqueda universal que coordina búsquedas en toda la aplicación
    y determina las relaciones de cada item/tag
    """

    def __init__(self, db_manager):
        """
        Inicializa el motor de búsqueda

        Args:
            db_manager: Instancia de DBManager para acceso a base de datos
        """
        self.db = db_manager
        logger.info("UniversalSearchEngine initialized")

    def search_all(
        self,
        query: str,
        search_items: bool = True,
        search_tags: bool = False,
        limit: int = 1000
    ) -> List[SearchResult]:
        """
        Búsqueda universal en items y/o tags

        Args:
            query: Texto de búsqueda
            search_items: Si True, busca en items
            search_tags: Si True, busca en tags
            limit: Límite de resultados

        Returns:
            Lista de SearchResult con todas las relaciones
        """
        results = []

        if search_items:
            item_results = self.search_items(query, limit=limit)
            results.extend(item_results)

        if search_tags:
            tag_results = self.search_tags(query, limit=limit)
            results.extend(tag_results)

        logger.info(f"Universal search for '{query}': {len(results)} results")
        return results

    def search_items(self, query: str, limit: int = 1000, offset: int = 0) -> List[SearchResult]:
        """
        Busca items y obtiene todas sus relaciones

        Args:
            query: Texto de búsqueda
            limit: Límite de resultados
            offset: Número de resultados a saltar (para paginación)

        Returns:
            Lista de SearchResult para items
        """
        try:
            # Obtener items usando búsqueda FTS5 del DBManager
            raw_items = self.db.universal_search_items(query, limit=limit, offset=offset)

            results = []
            for item_data in raw_items:
                # Crear SearchResult con todas las relaciones
                result = SearchResult(
                    result_type=SearchResultType.ITEM,
                    id=item_data['id'],
                    name=item_data['label'],
                    content=item_data.get('content', ''),
                    icon=item_data.get('icon', ''),
                    color=item_data.get('color', ''),
                    description=item_data.get('description', ''),

                    # Relaciones (vienen del query SQL)
                    proyectos=self._parse_comma_separated(item_data.get('proyectos')),
                    areas=self._parse_comma_separated(item_data.get('areas')),
                    categoria=item_data.get('categoria_name'),
                    tabla=item_data.get('tabla_name'),
                    procesos=self._parse_comma_separated(item_data.get('procesos')),
                    lista=item_data.get('lista_name'),

                    # Tags del item
                    tags=self._parse_comma_separated(item_data.get('tags')),

                    # Metadata
                    use_count=item_data.get('use_count', 0),
                    created_at=item_data.get('created_at', ''),
                    updated_at=item_data.get('updated_at', ''),
                    last_used=item_data.get('last_used', ''),
                    is_sensitive=bool(item_data.get('is_sensitive', False)),
                    is_favorite=bool(item_data.get('is_favorite', False))
                )
                results.append(result)

            logger.debug(f"Found {len(results)} items for query '{query}'")
            return results

        except Exception as e:
            logger.error(f"Error searching items: {e}", exc_info=True)
            return []

    def search_tags(self, query: str, limit: int = 1000) -> List[SearchResult]:
        """
        Busca tags en todas las tablas de tags

        Args:
            query: Texto de búsqueda
            limit: Límite de resultados

        Returns:
            Lista de SearchResult para tags
        """
        try:
            # Obtener tags de todas las tablas
            raw_tags = self.db.universal_search_tags(query, limit=limit)

            results = []
            for tag_data in raw_tags:
                # Determinar tipo de tag
                tag_type_str = tag_data.get('tag_type', 'item_tag')
                if tag_type_str == 'item_tag':
                    result_type = SearchResultType.TAG
                elif tag_type_str == 'category_tag':
                    result_type = SearchResultType.CATEGORY_TAG
                elif tag_type_str == 'project_tag':
                    result_type = SearchResultType.PROJECT_TAG
                elif tag_type_str == 'area_tag':
                    result_type = SearchResultType.AREA_TAG
                else:
                    result_type = SearchResultType.TAG

                result = SearchResult(
                    result_type=result_type,
                    id=tag_data['id'],
                    name=tag_data['name'],
                    content=f"Tag: {tag_data['name']}",
                    icon='🏷️',
                    color=tag_data.get('color', '#888888'),
                    description=tag_data.get('description', ''),

                    # Para tags, las relaciones se obtienen diferente
                    # Por ahora dejamos vacío, se puede expandir luego
                    tags=[],

                    # Metadata
                    use_count=tag_data.get('usage_count', 0),
                    created_at=tag_data.get('created_at', ''),
                    updated_at=tag_data.get('updated_at', '')
                )
                results.append(result)

            logger.debug(f"Found {len(results)} tags for query '{query}'")
            return results

        except Exception as e:
            logger.error(f"Error searching tags: {e}", exc_info=True)
            return []

    def get_item_relationships(self, item_id: int) -> ItemRelationships:
        """
        Obtiene todas las relaciones de un item específico

        Args:
            item_id: ID del item

        Returns:
            ItemRelationships con todas las relaciones
        """
        try:
            item_data = self.db.get_item_relationships(item_id)

            if not item_data:
                return ItemRelationships()

            return ItemRelationships(
                proyectos=self._parse_comma_separated(item_data.get('proyectos')),
                areas=self._parse_comma_separated(item_data.get('areas')),
                categoria=item_data.get('categoria'),
                tabla=item_data.get('tabla'),
                procesos=self._parse_comma_separated(item_data.get('procesos')),
                lista=item_data.get('lista')
            )

        except Exception as e:
            logger.error(f"Error getting item relationships: {e}", exc_info=True)
            return ItemRelationships()

    def apply_filters(
        self,
        results: List[SearchResult],
        entity_filters: Dict[str, bool],
        tag_filters: List[str] = None
    ) -> List[SearchResult]:
        """
        Aplica filtros a los resultados de búsqueda

        Args:
            results: Lista de resultados
            entity_filters: Dict con filtros por tipo de entidad
            tag_filters: Lista de tags requeridos (lógica AND)

        Returns:
            Lista filtrada de SearchResult
        """
        filtered = results

        # Aplicar filtro de entidades
        if entity_filters:
            filtered = [
                r for r in filtered
                if r.matches_entity_filter(entity_filters)
            ]

        # Aplicar filtro de tags
        if tag_filters:
            filtered = [
                r for r in filtered
                if r.has_all_tags(tag_filters)
            ]

        logger.debug(f"Applied filters: {len(results)} -> {len(filtered)} results")
        return filtered

    def get_most_used(self, limit: int = 100) -> List[SearchResult]:
        """
        Obtiene los items más usados

        Args:
            limit: Límite de resultados

        Returns:
            Lista de SearchResult ordenados por uso
        """
        try:
            raw_items = self.db.get_most_used_items(limit=limit)

            results = []
            for item_data in raw_items:
                result = SearchResult(
                    result_type=SearchResultType.ITEM,
                    id=item_data['id'],
                    name=item_data['label'],
                    content=item_data.get('content', ''),
                    icon=item_data.get('icon', ''),
                    color=item_data.get('color', ''),
                    description=item_data.get('description', ''),

                    proyectos=self._parse_comma_separated(item_data.get('proyectos')),
                    areas=self._parse_comma_separated(item_data.get('areas')),
                    categoria=item_data.get('categoria_name'),
                    tabla=item_data.get('tabla_name'),
                    procesos=self._parse_comma_separated(item_data.get('procesos')),
                    lista=item_data.get('lista_name'),

                    tags=self._parse_comma_separated(item_data.get('tags')),

                    use_count=item_data.get('use_count', 0),
                    created_at=item_data.get('created_at', ''),
                    updated_at=item_data.get('updated_at', ''),
                    last_used=item_data.get('last_used', ''),
                    is_sensitive=bool(item_data.get('is_sensitive', False)),
                    is_favorite=bool(item_data.get('is_favorite', False))
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error getting most used items: {e}", exc_info=True)
            return []

    def get_items_with_tags(self, limit: int = 1000) -> List[SearchResult]:
        """
        Obtiene items que tienen al menos un tag

        Args:
            limit: Límite de resultados

        Returns:
            Lista de SearchResult con tags
        """
        try:
            raw_items = self.db.get_items_with_tags(limit=limit)

            results = []
            for item_data in raw_items:
                result = SearchResult(
                    result_type=SearchResultType.ITEM,
                    id=item_data['id'],
                    name=item_data['label'],
                    content=item_data.get('content', ''),
                    icon=item_data.get('icon', ''),
                    color=item_data.get('color', ''),
                    description=item_data.get('description', ''),

                    proyectos=self._parse_comma_separated(item_data.get('proyectos')),
                    areas=self._parse_comma_separated(item_data.get('areas')),
                    categoria=item_data.get('categoria_name'),
                    tabla=item_data.get('tabla_name'),
                    procesos=self._parse_comma_separated(item_data.get('procesos')),
                    lista=item_data.get('lista_name'),

                    tags=self._parse_comma_separated(item_data.get('tags')),

                    use_count=item_data.get('use_count', 0),
                    created_at=item_data.get('created_at', ''),
                    updated_at=item_data.get('updated_at', ''),
                    last_used=item_data.get('last_used', ''),
                    is_sensitive=bool(item_data.get('is_sensitive', False)),
                    is_favorite=bool(item_data.get('is_favorite', False))
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error getting items with tags: {e}", exc_info=True)
            return []

    def get_recent_items(self, limit: int = 100) -> List[SearchResult]:
        """
        Obtiene items recientes

        Args:
            limit: Límite de resultados

        Returns:
            Lista de SearchResult ordenados por fecha
        """
        try:
            raw_items = self.db.get_recent_items(limit=limit)

            results = []
            for item_data in raw_items:
                result = SearchResult(
                    result_type=SearchResultType.ITEM,
                    id=item_data['id'],
                    name=item_data['label'],
                    content=item_data.get('content', ''),
                    icon=item_data.get('icon', ''),
                    color=item_data.get('color', ''),
                    description=item_data.get('description', ''),

                    proyectos=self._parse_comma_separated(item_data.get('proyectos')),
                    areas=self._parse_comma_separated(item_data.get('areas')),
                    categoria=item_data.get('categoria_name'),
                    tabla=item_data.get('tabla_name'),
                    procesos=self._parse_comma_separated(item_data.get('procesos')),
                    lista=item_data.get('lista_name'),

                    tags=self._parse_comma_separated(item_data.get('tags')),

                    use_count=item_data.get('use_count', 0),
                    created_at=item_data.get('created_at', ''),
                    updated_at=item_data.get('updated_at', ''),
                    last_used=item_data.get('last_used', ''),
                    is_sensitive=bool(item_data.get('is_sensitive', False)),
                    is_favorite=bool(item_data.get('is_favorite', False))
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error getting recent items: {e}", exc_info=True)
            return []

    def extract_unique_tags(self, results: List[SearchResult]) -> List[tuple]:
        """
        Extrae tags únicos de los resultados con conteo

        Args:
            results: Lista de resultados

        Returns:
            Lista de tuplas (tag_name, count) ordenada por count descendente
        """
        tag_counts: Dict[str, int] = {}

        for result in results:
            for tag in result.tags:
                tag_lower = tag.lower()
                tag_counts[tag_lower] = tag_counts.get(tag_lower, 0) + 1

        # Ordenar por count descendente
        sorted_tags = sorted(
            tag_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_tags

    def _parse_comma_separated(self, value: Optional[str]) -> List[str]:
        """
        Parsea string separado por comas a lista

        Args:
            value: String con valores separados por comas

        Returns:
            Lista de strings
        """
        if not value:
            return []

        # Manejar tanto strings como listas
        if isinstance(value, list):
            return value

        # Split por coma y limpiar espacios
        items = [item.strip() for item in str(value).split(',') if item.strip()]
        return items

    def get_statistics(self, results: List[SearchResult]) -> Dict[str, Any]:
        """
        Calcula estadísticas de los resultados

        Args:
            results: Lista de resultados

        Returns:
            Dict con estadísticas
        """
        stats = {
            'total': len(results),
            'items': sum(1 for r in results if r.result_type == SearchResultType.ITEM),
            'tags': sum(1 for r in results if r.result_type != SearchResultType.ITEM),
            'with_proyectos': sum(1 for r in results if r.proyectos),
            'with_areas': sum(1 for r in results if r.areas),
            'with_categorias': sum(1 for r in results if r.categoria),
            'with_tablas': sum(1 for r in results if r.tabla),
            'with_procesos': sum(1 for r in results if r.procesos),
            'with_listas': sum(1 for r in results if r.lista),
            'unique_tags': len(self.extract_unique_tags(results)),
            'favorites': sum(1 for r in results if r.is_favorite),
            'sensitive': sum(1 for r in results if r.is_sensitive)
        }

        return stats

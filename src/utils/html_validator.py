"""
Validador de contenido HTML para items WEB_STATIC.
Incluye validación de sintaxis, tamaño y patrones peligrosos.
"""

import re
from html.parser import HTMLParser
from typing import Tuple, List
from src.utils.constants import (
    WEB_STATIC_SIZE_SOFT_LIMIT,
    WEB_STATIC_SIZE_HARD_LIMIT,
    DANGEROUS_PATTERNS
)


class HTMLSyntaxValidator(HTMLParser):
    """Parser HTML para validación de sintaxis básica mejorado"""

    def __init__(self):
        super().__init__()
        self.errors = []
        self.tag_stack = []
        # Tags que pueden auto-cerrarse (void elements HTML5)
        self.void_elements = {
            'area', 'base', 'br', 'col', 'embed', 'hr', 'img',
            'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'
        }
        # Tags opcionales que pueden no cerrarse en HTML5
        self.optional_close = {'p', 'li', 'dt', 'dd', 'option', 'tbody', 'thead', 'tfoot', 'tr', 'td', 'th'}

    def handle_starttag(self, tag, attrs):
        """Registra tags de apertura"""
        tag = tag.lower()

        # No agregar void elements al stack
        if tag in self.void_elements:
            return

        self.tag_stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        """Maneja tags auto-cerrados como <img />, <meta />"""
        # No hacer nada, estos son válidos y no necesitan tracking
        # HTMLParser ya maneja esto correctamente
        pass

    def handle_endtag(self, tag):
        """Valida cierre de tags con búsqueda en el stack"""
        tag = tag.lower()

        # Void elements no deberían tener cierre, pero si lo tienen, ignorar
        if tag in self.void_elements:
            return

        # Si el stack está vacío, es un error (pero solo si no es un tag opcional)
        if not self.tag_stack:
            # Ignorar cierre de tags opcionales sin apertura (HTML5 flexible)
            if tag not in self.optional_close:
                self.errors.append(f"Tag de cierre sin apertura: </{tag}>")
            return

        # Buscar el tag en el stack (permite HTML5 con tags opcionales)
        if tag in self.tag_stack:
            # Encontrar la posición del tag
            idx = len(self.tag_stack) - 1
            while idx >= 0 and self.tag_stack[idx] != tag:
                # Si hay tags con cierre opcional entre medio, auto-cerrarlos silenciosamente
                if self.tag_stack[idx] not in self.optional_close:
                    # Solo reportar error si no es un tag opcional común
                    self.errors.append(
                        f"Tag mal cerrado: esperaba </{self.tag_stack[idx]}>, encontró </{tag}>"
                    )
                    return
                idx -= 1

            # Remover el tag y todos los opcionales antes (pop desde idx)
            if idx >= 0:
                self.tag_stack = self.tag_stack[:idx]
        else:
            # Tag no encontrado en el stack - solo reportar si no es opcional
            if tag not in self.optional_close:
                self.errors.append(f"Tag de cierre sin apertura correspondiente: </{tag}>")

    def error(self, message):
        """Captura errores del parser"""
        # Ignorar algunos warnings menores del parser
        if "unknown declaration" not in message.lower():
            self.errors.append(f"Error de sintaxis: {message}")


def validate_html_syntax(html_content: str) -> Tuple[bool, List[str]]:
    """
    Valida sintaxis HTML básica.

    Args:
        html_content: Contenido HTML a validar

    Returns:
        Tupla de (es_válido, lista_de_errores)
    """
    if not html_content.strip():
        return False, ["El contenido HTML está vacío"]

    parser = HTMLSyntaxValidator()

    try:
        parser.feed(html_content)
    except Exception as e:
        return False, [f"Error al parsear HTML: {str(e)}"]

    # Verificar tags sin cerrar (solo tags críticos, no opcionales)
    unclosed_critical_tags = [tag for tag in parser.tag_stack if tag not in parser.optional_close]
    if unclosed_critical_tags:
        parser.errors.append(f"Tags críticos sin cerrar: {', '.join(unclosed_critical_tags)}")

    is_valid = len(parser.errors) == 0
    return is_valid, parser.errors


def validate_html_size(content: str) -> Tuple[bool, str, str]:
    """
    Valida tamaño del contenido HTML.

    Args:
        content: Contenido HTML a validar

    Returns:
        Tupla de (es_válido, nivel_advertencia, mensaje)
        nivel_advertencia: 'ok' | 'warning' | 'error'
    """
    size_bytes = len(content.encode('utf-8'))
    size_kb = size_bytes / 1024

    if size_bytes > WEB_STATIC_SIZE_HARD_LIMIT:
        return False, 'error', f"Contenido demasiado grande: {size_kb:.1f} KB (máximo: 500 KB)"

    if size_bytes > WEB_STATIC_SIZE_SOFT_LIMIT:
        return True, 'warning', f"Contenido grande: {size_kb:.1f} KB. Se recomienda optimizar."

    return True, 'ok', f"Tamaño: {size_kb:.1f} KB"


def scan_dangerous_patterns(html: str) -> Tuple[bool, List[str]]:
    """
    Escanea patrones potencialmente peligrosos en HTML.

    Args:
        html: Contenido HTML a escanear

    Returns:
        Tupla de (es_seguro, lista_de_advertencias)
    """
    warnings = []

    for pattern in DANGEROUS_PATTERNS:
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            warnings.append(f"⚠️ Patrón sospechoso detectado: {pattern} ({len(matches)} coincidencias)")

    is_safe = len(warnings) == 0
    return is_safe, warnings


def sanitize_html_for_rendering(html_content: str) -> str:
    """
    Inyecta Content Security Policy (CSP) en HTML para renderizado seguro.

    Args:
        html_content: HTML original del usuario

    Returns:
        HTML con CSP meta tag inyectado
    """
    csp_meta = '''<meta http-equiv="Content-Security-Policy"
          content="default-src 'self';
                   script-src 'unsafe-inline' 'unsafe-eval';
                   style-src 'unsafe-inline';
                   img-src data: blob:;
                   connect-src 'none';
                   font-src 'none';
                   object-src 'none';
                   media-src 'none';
                   frame-src 'none';">'''

    # Insertar CSP después de <head> o al inicio
    html_lower = html_content.lower()

    if '<head>' in html_lower:
        # Buscar posición case-insensitive
        head_pos = html_lower.find('<head>')
        head_tag = html_content[head_pos:head_pos+6]
        html_content = html_content.replace(head_tag, f'{head_tag}\n{csp_meta}', 1)
    elif '<html>' in html_lower:
        # Buscar posición case-insensitive
        html_pos = html_lower.find('<html>')
        html_tag = html_content[html_pos:html_pos+6]
        html_content = html_content.replace(html_tag, f'{html_tag}\n<head>\n{csp_meta}\n</head>', 1)
    else:
        # Si no hay estructura HTML, envolver todo
        html_content = f'<!DOCTYPE html>\n<html>\n<head>\n{csp_meta}\n</head>\n<body>\n{html_content}\n</body>\n</html>'

    return html_content


def validate_web_static_content(html_content: str) -> dict:
    """
    Validación completa de contenido WEB_STATIC.

    Args:
        html_content: Contenido HTML a validar

    Returns:
        Diccionario con resultados de validación:
        {
            'is_valid': bool,           # True si pasa todas las validaciones sin warnings
            'syntax_valid': bool,       # True si sintaxis HTML es válida
            'syntax_errors': List[str], # Lista de errores de sintaxis
            'size_valid': bool,         # True si tamaño no excede hard limit
            'size_level': str,          # 'ok' | 'warning' | 'error'
            'size_message': str,        # Mensaje descriptivo de tamaño
            'security_safe': bool,      # True si no hay patrones peligrosos
            'security_warnings': List[str], # Lista de advertencias de seguridad
            'can_save': bool            # True si puede guardarse (sintaxis válida + tamaño OK)
        }
    """
    # Validación de sintaxis
    syntax_valid, syntax_errors = validate_html_syntax(html_content)

    # Validación de tamaño
    size_valid, size_level, size_message = validate_html_size(html_content)

    # Escaneo de seguridad
    security_safe, security_warnings = scan_dangerous_patterns(html_content)

    # Puede guardarse si sintaxis es válida Y tamaño no excede hard limit
    can_save = syntax_valid and size_valid

    # Es completamente válido si pasa todas las validaciones sin warnings
    is_valid = syntax_valid and size_level == 'ok' and security_safe

    return {
        'is_valid': is_valid,
        'syntax_valid': syntax_valid,
        'syntax_errors': syntax_errors,
        'size_valid': size_valid,
        'size_level': size_level,
        'size_message': size_message,
        'security_safe': security_safe,
        'security_warnings': security_warnings,
        'can_save': can_save
    }

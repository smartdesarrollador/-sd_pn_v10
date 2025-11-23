"""
Application constants
"""

import re

APP_NAME = "Widget Sidebar"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Widget Sidebar Team"

# Item Types
ITEM_TYPES = ['CODE', 'URL', 'PATH', 'TEXT', 'WEB_STATIC']

# Límites de tamaño para WEB_STATIC
WEB_STATIC_SIZE_SOFT_LIMIT = 100 * 1024  # 100 KB - advertencia
WEB_STATIC_SIZE_HARD_LIMIT = 500 * 1024  # 500 KB - rechazo

# Patrones peligrosos para validación de seguridad
DANGEROUS_PATTERNS = [
    r'<iframe',                          # Iframes
    r'fetch\s*\(',                       # Llamadas fetch
    r'XMLHttpRequest',                   # AJAX
    r'import\s+.*from',                  # ES6 imports externos
    r'<script[^>]*src=',                 # Scripts externos
    r'<link[^>]*href=["\']https?://',   # CSS externos
    r'<img[^>]*src=["\']https?://',     # Imágenes externas
    r'eval\s*\(',                        # eval()
    r'Function\s*\(',                    # Constructor Function
    r'localStorage',                     # localStorage
    r'sessionStorage',                   # sessionStorage
    r'document\.cookie',                 # Acceso a cookies
]

# Íconos para tipos de items
ITEM_TYPE_ICONS = {
    'CODE': '💻',
    'URL': '🔗',
    'PATH': '📁',
    'TEXT': '📝',
    'WEB_STATIC': '🌐'
}

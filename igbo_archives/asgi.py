"""
ASGI config for igbo_archives project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'igbo_archives.settings')

# Enable SQLite WAL mode for better performance
from igbo_archives.sqlite_wal import enable_wal_mode
enable_wal_mode()

application = get_asgi_application()


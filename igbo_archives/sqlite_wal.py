"""
SQLite WAL Mode Configuration for 1GB RAM constraint.
Enables Write-Ahead Logging for better concurrency.
"""
import sqlite3
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)


def enable_wal_mode():
    """Enable SQLite WAL mode with optimized settings for 1GB RAM."""
    db_path = Path(__file__).resolve().parent.parent / 'db.sqlite3'
    
    if not db_path.exists():
        if settings.DEBUG:
            logger.debug("Database file does not exist yet. WAL mode will be enabled on first migration.")
        return None
    
    conn = None
    cursor = None
    journal_result = None
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Enable WAL mode
        try:
            cursor.execute('PRAGMA journal_mode=WAL;')
            journal_result = cursor.fetchone()
            if journal_result and journal_result[0] != 'wal':
                logger.warning(f"Failed to enable WAL mode. Current mode: {journal_result[0]}")
        except Exception as e:
            logger.warning(f"Failed to set journal_mode=WAL: {e}", exc_info=settings.DEBUG)
        
        # Configure other PRAGMAs with error handling
        pragmas = [
            ('synchronous', 'NORMAL'),
            ('cache_size', '-32000'),  # 32MB - optimized for 1GB RAM
            ('temp_store', 'MEMORY'),
            ('mmap_size', '67108864'),  # 64MB - optimized for 1GB RAM
            ('busy_timeout', '5000'),  # 5 second timeout for locks
            ('foreign_keys', 'ON'),
        ]
        
        for pragma_name, pragma_value in pragmas:
            try:
                cursor.execute(f'PRAGMA {pragma_name}={pragma_value};')
            except Exception as e:
                logger.warning(f"Failed to set PRAGMA {pragma_name}={pragma_value}: {e}", exc_info=settings.DEBUG)
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error configuring SQLite WAL mode: {e}", exc_info=settings.DEBUG)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return journal_result[0] if journal_result else None

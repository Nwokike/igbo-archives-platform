"""
SQLite WAL Mode Configuration for 1GB RAM constraint.
Enables Write-Ahead Logging for better concurrency.
"""
import sqlite3
from pathlib import Path


def enable_wal_mode():
    """Enable SQLite WAL mode with optimized settings for 1GB RAM."""
    db_path = Path(__file__).resolve().parent.parent / 'db.sqlite3'
    
    if not db_path.exists():
        return None
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    journal_result = None
    
    try:
        cursor.execute('PRAGMA journal_mode=WAL;')
        journal_result = cursor.fetchone()
        
        cursor.execute('PRAGMA synchronous=NORMAL;')
        cursor.execute('PRAGMA cache_size=-32000;')  # 32MB - optimized for 1GB RAM
        cursor.execute('PRAGMA temp_store=MEMORY;')
        cursor.execute('PRAGMA mmap_size=67108864;')  # 64MB - optimized for 1GB RAM
        cursor.execute('PRAGMA busy_timeout=5000;')  # 5 second timeout for locks
        cursor.execute('PRAGMA foreign_keys=ON;')
    finally:
        cursor.close()
        conn.close()
    
    return journal_result[0] if journal_result else None

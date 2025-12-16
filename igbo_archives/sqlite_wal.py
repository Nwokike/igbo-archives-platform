import sqlite3
import os
from pathlib import Path

def enable_wal_mode():
    db_path = Path(__file__).resolve().parent.parent / 'db.sqlite3'
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute('PRAGMA journal_mode=WAL;')
        cursor.execute('PRAGMA synchronous=NORMAL;')
        cursor.execute('PRAGMA cache_size=-64000;')
        cursor.execute('PRAGMA temp_store=MEMORY;')
        cursor.execute('PRAGMA mmap_size=134217728;')
        result = cursor.fetchone()
        conn.close()
        return result
    return None

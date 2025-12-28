#!/usr/bin/env python
"""
Database backup script for Igbo Archives.
Backs up SQLite database to Cloudflare R2.

Run as cron job: 0 2 * * * /path/to/venv/bin/python /path/to/backup_to_r2.py
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'igbo_archives.settings')

import django
django.setup()

from django.conf import settings


def backup_database():
    """Backup SQLite database to R2."""
    import boto3
    from botocore.client import Config
    
    # Check R2 credentials
    access_key = getattr(settings, 'R2_ACCESS_KEY_ID', '')
    secret_key = getattr(settings, 'R2_SECRET_ACCESS_KEY', '')
    endpoint = getattr(settings, 'R2_ENDPOINT_URL', '')
    
    if not all([access_key, secret_key, endpoint]):
        print("Error: R2 credentials not configured")
        return False
    
    # Database path
    db_path = BASE_DIR / 'db.sqlite3'
    if not db_path.exists():
        print("Error: Database file not found")
        return False
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"backups/db_backup_{timestamp}.sqlite3"
    
    try:
        # Initialize S3 client for R2
        s3 = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4'),
        )
        
        # Upload to R2
        bucket = 'igboarchives-backup'
        
        with open(db_path, 'rb') as f:
            s3.upload_fileobj(f, bucket, backup_name)
        
        print(f"Success: Backup uploaded to {bucket}/{backup_name}")
        
        # Clean up old backups (keep last 7)
        cleanup_old_backups(s3, bucket, keep=7)
        
        return True
        
    except Exception as e:
        print(f"Error: Backup failed - {e}")
        return False


def cleanup_old_backups(s3, bucket: str, keep: int = 7):
    """Remove old backups, keeping the most recent ones."""
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix='backups/')
        
        if 'Contents' not in response:
            return
        
        # Sort by last modified, newest first
        objects = sorted(
            response['Contents'],
            key=lambda x: x['LastModified'],
            reverse=True
        )
        
        # Delete old backups
        for obj in objects[keep:]:
            s3.delete_object(Bucket=bucket, Key=obj['Key'])
            print(f"Deleted old backup: {obj['Key']}")
            
    except Exception as e:
        print(f"Warning: Cleanup failed - {e}")


if __name__ == '__main__':
    success = backup_database()
    sys.exit(0 if success else 1)

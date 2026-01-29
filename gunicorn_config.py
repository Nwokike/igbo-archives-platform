"""
Gunicorn configuration for Igbo Archives
Optimized for 1GB RAM Google Cloud VM deployment
"""
import multiprocessing

# Server socket
bind = "unix:/tmp/igboarchives.sock"
backlog = 256

# Worker processes - cap at 2 for 1GB RAM constraint
workers = min(2, (multiprocessing.cpu_count() * 2) + 1)
worker_class = "sync"  # Use sync for SQLite (avoid gevent with SQLite)
worker_connections = 100
timeout = 30
keepalive = 2

# Memory management
max_requests = 500  # Restart worker after 500 requests to prevent memory leaks
max_requests_jitter = 50  # Add randomness to prevent all workers restarting at once

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Process naming
proc_name = "igboarchives"

# Server mechanics
preload_app = True
daemon = False

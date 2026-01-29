"""
IndexNow API Integration
Instantly notify search engines (Bing, Yandex, etc.) when content is published or updated
"""
import requests
import uuid
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


def generate_api_key():
    """Generate a unique API key for IndexNow"""
    return str(uuid.uuid4())


def get_indexnow_key():
    """Get IndexNow API key from settings. Returns None if not configured."""
    key = getattr(settings, 'INDEXNOW_API_KEY', None) or os.getenv('INDEXNOW_API_KEY')
    if not key:
        logger.error("INDEXNOW_API_KEY is not set. Generate with: python -c \"import uuid; print(uuid.uuid4())\"")
        return None
    return key


def submit_url_to_indexnow(url, host=None):
    """
    Submit a URL to IndexNow API for immediate indexing
    
    Args:
        url: Full URL to submit (e.g., https://igboarchives.com/insights/my-post/)
        host: Domain name (e.g., igboarchives.com)
    """
    api_key = get_indexnow_key()
    
    if not host:
        # Extract host from URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.netloc
    
        # IndexNow API endpoint (can use Bing, Yandex, or others)
    endpoint = getattr(settings, 'INDEXNOW_API_URL', "https://api.indexnow.org/indexnow")
    
    payload = {
        "host": host,
        "key": api_key,
        "urlList": [url]
    }
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code in [200, 202]:
            logger.info(f"Successfully submitted to IndexNow: {url}")
            return True
        else:
            logger.error(f"IndexNow submission failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error submitting to IndexNow: {str(e)}")
        return False


def submit_urls_bulk(urls, host=None):
    """
    Submit multiple URLs to IndexNow at once (up to 10,000 URLs)
    
    Args:
        urls: List of full URLs
        host: Domain name
    """
    api_key = get_indexnow_key()
    
    if not host and urls:
        from urllib.parse import urlparse
        parsed = urlparse(urls[0])
        host = parsed.netloc
    
    endpoint = getattr(settings, 'INDEXNOW_API_URL', "https://api.indexnow.org/indexnow")
    
    # IndexNow allows up to 10,000 URLs per request
    for i in range(0, len(urls), 10000):
        batch = urls[i:i+10000]
        
        payload = {
            "host": host,
            "key": api_key,
            "urlList": batch
        }
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code in [200, 202]:
                logger.info(f"Successfully submitted {len(batch)} URLs to IndexNow")
            else:
                logger.error(f"IndexNow bulk submission failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error submitting bulk URLs to IndexNow: {str(e)}")


class IndexNowClient:
    """Class wrapper for IndexNow API functions.
    
    Provides a class-based interface for IndexNow URL submission.
    Used by core/tasks.py for async URL submission.
    """
    
    def __init__(self):
        self.api_key = get_indexnow_key()
    
    def submit_url(self, url, host=None):
        """Submit a single URL to IndexNow."""
        return submit_url_to_indexnow(url, host)
    
    def submit_urls(self, urls, host=None):
        """Submit multiple URLs to IndexNow."""
        return submit_urls_bulk(urls, host)

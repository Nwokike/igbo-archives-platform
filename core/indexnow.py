"""
IndexNow API Integration
Instantly notify search engines (Bing, Yandex, etc.) when content is published or updated.

IndexNow Protocol requires:
1. An API key set in INDEXNOW_API_KEY env var
2. A key verification file served at https://{host}/{key}.txt (handled by core.views.indexnow_key_verification)
3. Submissions via POST to https://api.indexnow.org/indexnow with keyLocation
"""
import requests
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def get_indexnow_key():
    """Get IndexNow API key from settings. Returns None if not configured."""
    key = getattr(settings, 'INDEXNOW_API_KEY', None) or os.getenv('INDEXNOW_API_KEY')
    if not key:
        logger.warning("INDEXNOW_API_KEY is not set. Generate with: python -c \"import uuid; print(uuid.uuid4().hex)\"")
        return None
    return key


def submit_url_to_indexnow(url, host=None):
    """
    Submit a URL to IndexNow API for immediate indexing.
    
    Args:
        url: Full URL to submit (e.g., https://igboarchives.com.ng/lore/my-post/)
        host: Domain name (e.g., igboarchives.com.ng)
    """
    api_key = get_indexnow_key()
    if not api_key:
        return False
    
    if not host:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.netloc
    
    endpoint = getattr(settings, 'INDEXNOW_API_URL', "https://api.indexnow.org/indexnow")
    key_location = f"https://{host}/{api_key}.txt"
    
    payload = {
        "host": host,
        "key": api_key,
        "keyLocation": key_location,
        "urlList": [url]
    }
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={'Content-Type': 'application/json; charset=utf-8'},
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
    Submit multiple URLs to IndexNow at once (up to 10,000 URLs per request).
    
    Args:
        urls: List of full URLs
        host: Domain name
    """
    api_key = get_indexnow_key()
    if not api_key:
        return False
    
    if not host and urls:
        from urllib.parse import urlparse
        parsed = urlparse(urls[0])
        host = parsed.netloc
    
    endpoint = getattr(settings, 'INDEXNOW_API_URL', "https://api.indexnow.org/indexnow")
    key_location = f"https://{host}/{api_key}.txt"
    
    for i in range(0, len(urls), 10000):
        batch = urls[i:i+10000]
        
        payload = {
            "host": host,
            "key": api_key,
            "keyLocation": key_location,
            "urlList": batch
        }
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers={'Content-Type': 'application/json; charset=utf-8'},
                timeout=30
            )
            
            if response.status_code in [200, 202]:
                logger.info(f"Successfully submitted {len(batch)} URLs to IndexNow")
            else:
                logger.error(f"IndexNow bulk submission failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error submitting bulk URLs to IndexNow: {str(e)}")
    
    return True

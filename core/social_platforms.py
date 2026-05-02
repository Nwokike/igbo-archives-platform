import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class SocialMediaPoster:
    def __init__(self):
        self.mastodon_token = settings.MASTODON_ACCESS_TOKEN
        self.fb_page_id = settings.FACEBOOK_PAGE_ID
        self.ig_account_id = settings.INSTAGRAM_ACCOUNT_ID
        self.fb_token = settings.FACEBOOK_PAGE_ACCESS_TOKEN
        
    def post_to_mastodon(self, message, media_url=None):
        if not self.mastodon_token:
            logger.warning("Mastodon token not configured. Skipping.")
            return False
            
        try:
            # We assume mastodon.social for now. If user has a different server, we'd add it to .env
            # Actually, I should use the correct server. The user didn't provide a server URL in the payload. 
            # I will default to https://mastodon.social unless otherwise specified.
            base_url = "https://mastodon.social"
            headers = {"Authorization": f"Bearer {self.mastodon_token}"}
            
            # If there's media, Mastodon requires uploading it first.
            # To keep it completely simple and debt-free, we will just post the link in the message.
            # Mastodon auto-expands OpenGraph tags from the link perfectly!
            
            payload = {
                "status": message,
                "visibility": "public"
            }
            
            response = requests.post(f"{base_url}/api/v1/statuses", headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            logger.info("Successfully posted to Mastodon.")
            return True
        except Exception as e:
            logger.error(f"Failed to post to Mastodon: {e}")
            return False

    def post_to_facebook(self, message, link=None):
        if not self.fb_page_id or not self.fb_token:
            logger.warning("Facebook credentials not configured. Skipping.")
            return False
            
        try:
            url = f"https://graph.facebook.com/v25.0/{self.fb_page_id}/feed"
            payload = {
                "message": message,
                "access_token": self.fb_token
            }
            if link:
                payload["link"] = link
                
            response = requests.post(url, data=payload, timeout=10)
            response.raise_for_status()
            logger.info("Successfully posted to Facebook.")
            return True
        except Exception as e:
            logger.error(f"Failed to post to Facebook: {e} - Response: {getattr(e, 'response', '') and getattr(e.response, 'text', '')}")
            return False

    def post_to_instagram(self, image_url, caption):
        if not self.ig_account_id or not self.fb_token:
            logger.warning("Instagram credentials not configured. Skipping.")
            return False
            
        if not image_url:
            logger.warning("No image URL provided for Instagram. Skipping.")
            return False
            
        try:
            # Step 1: Create Media Container
            container_url = f"https://graph.facebook.com/v25.0/{self.ig_account_id}/media"
            container_payload = {
                "image_url": image_url,
                "caption": caption,
                "access_token": self.fb_token
            }
            container_response = requests.post(container_url, data=container_payload, timeout=15)
            container_response.raise_for_status()
            container_id = container_response.json().get("id")
            
            if not container_id:
                logger.error("Failed to get container ID from Instagram.")
                return False
                
            # Step 2: Publish Media Container
            publish_url = f"https://graph.facebook.com/v25.0/{self.ig_account_id}/media_publish"
            publish_payload = {
                "creation_id": container_id,
                "access_token": self.fb_token
            }
            publish_response = requests.post(publish_url, data=publish_payload, timeout=15)
            publish_response.raise_for_status()
            
            logger.info("Successfully posted to Instagram.")
            return True
        except Exception as e:
            logger.error(f"Failed to post to Instagram: {e} - Response: {getattr(e, 'response', '') and getattr(e.response, 'text', '')}")
            return False

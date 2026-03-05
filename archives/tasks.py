"""
Background tasks for the archives app.
Uses Huey for async processing of email notifications.
"""
import logging
from django_huey import db_task
from django.conf import settings

logger = logging.getLogger(__name__)

@db_task()
def send_archive_notification_email(subject, message_body, staff_emails):
    """Send archive notification emails asynchronously via Django Huey."""
    try:
        from core.tasks import send_email_async
        send_email_async(
            subject=subject,
            message=message_body,
            recipient_list=staff_emails,
        )
        logger.info(f"Sent archive notification email: {subject}")
    except Exception as e:
        logger.error(f"Failed to send archive notification email: {e}")

@db_task()
def generate_explore_further_correlations(archive_id):
    """
    Background worker task to find related Books and Lore items based on an archive's content.
    Strict Llama-3 parsing using LiteLLM/Groq. Maximum 9 results.
    """
    try:
        from .models import Archive
        import litellm
        
        if not getattr(settings, 'GROQ_API_KEY', None):
            logger.warning("GROQ_API_KEY is not set. Skipping AI Explore Further generation.")
            return False
            
        archive = Archive.objects.get(pk=archive_id)
        
        # We'll pull titles and descriptions of all approved Books and Lore to pass to the model
        from books.models import BookRecommendation
        from lore.models import LorePost
        from django.core.cache import cache
        
        litellm.api_key = settings.GROQ_API_KEY
        
        books = BookRecommendation.objects.filter(is_approved=True).values('id', 'book_title', 'author')
        lores = LorePost.objects.filter(is_approved=True).values('id', 'title')
        
        if not books and not lores:
            return False
            
        book_catalog = "\n".join([f"Book {b['id']}: {b['book_title']} by {b['author']}" for b in books])
        lore_catalog = "\n".join([f"Lore {l['id']}: {l['title']}" for l in lores])

        prompt = f"""
We have an archive titled: "{archive.title}"
Description: {archive.description}
Tags/Keywords: {archive.category.name if archive.category else 'Cultural Archive'}

Based on this archive, which of the following Books and Lore items are HIGHLY related? 
Do not suggest tenuous connections. If none strongly match, say so. Max 9 items total.

BOOKS:
{book_catalog[:2000]} # Truncated for safety

LORE:
{lore_catalog[:2000]} # Truncated for safety

Format your response exactly as JSON:
{{
  "intro_paragraph": "A single sentence explaining why these items connect to the archive.",
  "book_ids": [integer array of matching book IDs],
  "lore_ids": [integer array of matching lore IDs]
}}
"""

        response = litellm.completion(
            model="groq/llama-3.1-8b-instant",  # Updated to strictly use free tier model requested by user
            messages=[
                {"role": "system", "content": "You are an expert curator of Igbo history and culture. You output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        
        intro = result.get('intro_paragraph', '')
        book_ids = result.get('book_ids', [])[:9] 
        lore_ids = result.get('lore_ids', [])[:9]
        
        # Save to cache (associated with archive) to avoid immediate model migrations for this
        cache_key = f'archive_correlations_{archive_id}'
        cache.set(cache_key, {
            'intro': intro,
            'book_ids': book_ids,
            'lore_ids': lore_ids
        }, timeout=60 * 60 * 24 * 30) # Cache for 30 days
        
        logger.info(f"AI Explorer mapped Archive {archive_id} to Books: {book_ids} and Lores: {lore_ids}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate Explore Further correlations for archive {archive_id}: {e}")
        return False

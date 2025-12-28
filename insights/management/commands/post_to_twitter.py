from django.core.management.base import BaseCommand
from insights.models import InsightPost
import tweepy
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Post approved insights to Twitter/X with images'
    
    def handle(self, *args, **options):
        # Check if Twitter API credentials are configured
        if not all([settings.TWITTER_API_KEY, settings.TWITTER_API_SECRET, 
                    settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_ACCESS_TOKEN_SECRET]):
            self.stdout.write(self.style.WARNING('Twitter API credentials not configured'))
            return
        
        # Initialize Twitter API v2 client
        client = tweepy.Client(
            consumer_key=settings.TWITTER_API_KEY,
            consumer_secret=settings.TWITTER_API_SECRET,
            access_token=settings.TWITTER_ACCESS_TOKEN,
            access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET
        )
        
        # Initialize API v1.1 for media upload
        auth = tweepy.OAuth1UserHandler(
            settings.TWITTER_API_KEY,
            settings.TWITTER_API_SECRET,
            settings.TWITTER_ACCESS_TOKEN,
            settings.TWITTER_ACCESS_TOKEN_SECRET
        )
        api_v1 = tweepy.API(auth)
        
        # Get posts to share (limit to 5 per run)
        posts = InsightPost.objects.filter(
            is_published=True,
            is_approved=True,
            posted_to_social=False
        )[:5]
        
        if not posts.exists():
            self.stdout.write('No new posts to share')
            return
        
        for post in posts:
            try:
                # Prepare tweet text
                excerpt = post.excerpt[:150] + '...' if len(post.excerpt) > 150 else post.excerpt
                tweet_text = f"{post.title}\n\n{excerpt}\n\n#Igbo #IgboArchives #IgboCulture\n\nhttps://igboarchives.com/insights/{post.slug}/"
                
                # Upload image if available
                media_ids = []
                if post.featured_image:
                    try:
                        image_path = post.featured_image.path
                        if os.path.exists(image_path):
                            # Upload media using v1.1 API
                            media = api_v1.media_upload(filename=image_path)
                            media_ids = [media.media_id]
                            self.stdout.write(f'Uploaded image for: {post.title}')
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'Could not upload image: {str(e)}'))
                
                # Create tweet with or without media
                if media_ids:
                    client.create_tweet(text=tweet_text, media_ids=media_ids)
                else:
                    client.create_tweet(text=tweet_text)
                
                # Mark as posted
                post.posted_to_social = True
                post.save()
                
                self.stdout.write(self.style.SUCCESS(f'Posted to Twitter/X: {post.title}'))
                
            except tweepy.TweepyException as e:
                self.stdout.write(self.style.ERROR(f'Twitter API error for {post.title}: {str(e)}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error posting {post.title}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Finished processing {posts.count()} post(s)'))

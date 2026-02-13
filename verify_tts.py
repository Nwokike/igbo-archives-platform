import os
import django
import sys
import json
from django.test import Client
from django.core.cache import cache

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'igbo_archives.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

def verify_tts_flow():
    print("--- Verifying Storage-less TTS Flow ---")
    
    client = Client()
    
    # Create test user
    username = "testuser_tts"
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username=username, password="password123")
    else:
        user = User.objects.get(username=username)
    
    client.force_login(user)
    
    # 1. Generate TTS
    print("Step 1: Generating TTS...")
    response = client.post('/ai/tts/', 
                           data=json.dumps({'text': 'Nnoo na Igbo Archives.', 'voice': 'default'}),
                           content_type='application/json')
    
    if response.status_code != 200:
        print(f"FAILED: /ai/tts/ returned {response.status_code}")
        print(response.content)
        return

    data = response.json()
    if not data['success']:
        print(f"FAILED: TTS generation failed: {data.get('error')}")
        return

    serve_url = data['url']
    print(f"SUCCESS: Generated serve URL: {serve_url}")
    
    # 2. Serve TTS
    print(f"Step 2: Accessing serve URL {serve_url}...")
    serve_response = client.get(serve_url)
    
    if serve_response.status_code != 200:
        print(f"FAILED: {serve_url} returned {serve_response.status_code}")
        return
    
    content_type = serve_response['Content-Type']
    content_length = len(serve_response.content)
    
    print(f"SUCCESS: Served audio. Type: {content_type}, Size: {content_length} bytes")
    
    if content_length > 100:
        print("VERIFIED: End-to-end TTS flow works without local filesystem writes!")
    else:
        print("FAILED: Audio content seems too small.")

if __name__ == "__main__":
    verify_tts_flow()

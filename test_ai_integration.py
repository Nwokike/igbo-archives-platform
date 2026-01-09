
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'igbo_archives.settings')
django.setup()

from ai.services.chat_service import chat_service
from ai.services.vision_service import vision_service
from ai.services.gemini_service import gemini_service

def test_ai():
    print("--- Starting AI Integration Test ---")
    
    # Test Chat Service
    print("\nTesting Chat Service (Standard)...")
    messages = [{'role': 'user', 'content': 'Hello, who are you and what is your purpose?'}]
    result = chat_service.chat(messages, use_web_search=False)
    if result['success']:
        print(f"✅ Chat Success! Response prefix: {result['content'][:100]}...")
    else:
        print(f"❌ Chat Failed: {result['content']}")

    # Test Gemini Service (Direct)
    print("\nTesting Gemini 3.0 Flash Direct...")
    gemini_result = gemini_service.chat([{'role': 'user', 'content': 'Confirm your model version.'}])
    if gemini_result['success']:
        print(f"✅ Gemini 3.0 Success! Model: {gemini_result.get('model')} Response: {gemini_result['content'][:100]}...")
    else:
        print(f"❌ Gemini Service Failed: {gemini_result['content']}")

    print("\n--- AI Integration Test Complete ---")

if __name__ == "__main__":
    test_ai()

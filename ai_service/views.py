from django.shortcuts import render

def ai_chat(request):
    return render(request, 'ai_service/chat.html')

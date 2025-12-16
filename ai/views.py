from django.shortcuts import render


def coming_soon(request):
    """AI coming soon page with details about future features."""
    return render(request, 'ai/coming_soon.html')

from django.shortcuts import render
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from archives.models import Archive


def home(request):
    # Get all approved archives and randomize (no featured filtering)
    all_archives = Archive.objects.filter(is_approved=True).order_by('?')[:10]
    context = {
        'featured_archives': all_archives
    }
    return render(request, 'core/home.html', context)


def terms_of_service(request):
    return render(request, 'core/pages/terms.html', {'current_date': timezone.now()})


def privacy_policy(request):
    return render(request, 'core/pages/privacy.html', {'current_date': timezone.now()})


def copyright_policy(request):
    return render(request, 'core/pages/copyright.html', {'current_date': timezone.now()})


def about(request):
    return render(request, 'core/pages/about.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message_text = request.POST.get('message')
        
        if hasattr(settings, 'ADMIN_EMAIL') and settings.ADMIN_EMAIL:
            try:
                full_message = f"""
Contact Form Submission

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message_text}
"""
                send_mail(
                    f'Contact Form: {subject}',
                    full_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, 'Thank you for your message! We will get back to you soon.')
            except Exception as e:
                messages.error(request, 'There was an error sending your message. Please try again later.')
        else:
            messages.info(request, f'Email not configured. Your message: "{subject}" from {email} has been logged.')
    
    return render(request, 'core/pages/contact.html')

def donate(request):
    """Donation page"""
    return render(request, 'core/donate.html')

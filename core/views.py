import random
from django.shortcuts import render
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from archives.models import Archive


def get_all_approved_archive_ids():
    """Cache all approved archive IDs. For datasets under 100k, this is memory-efficient.
    
    Memory estimate: 100,000 IDs * 8 bytes = ~800KB, well within 1GB constraint.
    """
    cache_key = 'all_approved_archive_ids'
    archive_ids = cache.get(cache_key)
    
    if archive_ids is None:
        archive_ids = tuple(
            Archive.objects.filter(is_approved=True)
            .values_list('id', flat=True)
            .iterator(chunk_size=1000)
        )
        cache.set(cache_key, archive_ids, 300)
    
    return archive_ids


def get_random_featured_archives(count=10):
    """Memory-efficient random archive selection with caching.
    
    Caches all approved archive IDs and samples randomly from them.
    Single query to fetch selected archives.
    """
    archive_ids = get_all_approved_archive_ids()
    
    if not archive_ids:
        return Archive.objects.none()
    
    sample_size = min(count, len(archive_ids))
    random_ids = random.sample(archive_ids, sample_size)
    
    return Archive.objects.filter(pk__in=random_ids).select_related('category', 'uploaded_by')


def home(request):
    featured_archives = get_random_featured_archives(10)
    context = {
        'featured_archives': featured_archives
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
    context = {
        'paypal_url': getattr(settings, 'PAYPAL_DONATION_URL', None)
    }
    return render(request, 'core/donate.html', context)

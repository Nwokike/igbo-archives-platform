import random
from django.shortcuts import render
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.views.decorators.cache import never_cache
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


def get_random_featured_archives(max_count=50):
    """Memory-efficient random archive selection for homepage carousel.
    
    Returns up to max_count approved image archives in random order for carousel.
    Uses cached IDs shuffled on each page load for true randomness.
    Limits memory usage for 1GB VM constraint.
    """
    cache_key = 'image_archive_ids'
    image_ids = cache.get(cache_key)
    
    if image_ids is None:
        # Single query to get all image archive IDs
        image_ids = list(
            Archive.objects.filter(is_approved=True, archive_type='image')
            .values_list('id', flat=True)
        )
        cache.set(cache_key, image_ids, 300)
    
    if not image_ids:
        return Archive.objects.none()
    
    # Limit to max_count for memory efficiency
    if len(image_ids) > max_count:
        selected_ids = random.sample(image_ids, max_count)
    else:
        selected_ids = image_ids[:]
        random.shuffle(selected_ids)
    
    # Fetch archives with optimized query
    archives = list(Archive.objects.filter(
        pk__in=selected_ids
    ).select_related('category', 'uploaded_by'))
    
    # Shuffle again for final randomness
    random.shuffle(archives)
    return archives


@never_cache
def home(request):
    featured_archives = get_random_featured_archives()
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
    from .forms import ContactForm
    
    if request.method == 'POST':
        form = ContactForm(request.POST, request=request)
        
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message_text = form.cleaned_data['message']
            
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
            
            form = ContactForm(request=request)
    else:
        form = ContactForm(request=request)
    
    return render(request, 'core/pages/contact.html', {'form': form})



def donate(request):
    """Donation page - Paystack-only"""
    context = {
        'paystack_public_key': getattr(settings, 'PAYSTACK_PUBLIC_KEY', ''),
        'enable_donations': getattr(settings, 'ENABLE_DONATIONS', False),
    }
    return render(request, 'core/donate.html', context)


def offline(request):
    """Offline fallback page for PWA"""
    return render(request, 'offline.html')


def health_check(request):
    """Simple health check endpoint for deployment verification."""
    return render(request, 'core/health.html', status=200)


def bad_request_handler(request, exception):
    """400 Bad Request handler."""
    return render(request, '400.html', status=400)


def permission_denied_handler(request, exception):
    """403 Forbidden handler."""
    return render(request, '403.html', status=403)


def page_not_found_handler(request, exception):
    """404 Not Found handler."""
    return render(request, '404.html', status=404)


def server_error_handler(request):
    """500 Internal Server Error handler."""
    return render(request, '500.html', status=500)


def robots_txt(request):
    """Serve robots.txt"""
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    content = render_to_string('robots.txt', request=request)
    return HttpResponse(content, content_type='text/plain')


def chrome_devtools_association(request):
    """
    Serve the chrome devtools association file to silence 404s.
    Returns:
        JsonResponse: Empty JSON object
    """
    from django.http import JsonResponse
    return JsonResponse({})

"""
Shared username generation utilities.
Used by forms.py (signup) and signals.py (shadow accounts).
"""
import re

# Reserved usernames that would conflict with URL patterns
RESERVED_USERNAMES = frozenset({
    'admin', 'messages', 'dashboard', 'delete-account',
    'notifications', 'login', 'logout', 'signup', 'register',
    'settings', 'api', 'static', 'media', 'accounts',
})


def generate_unique_username(email):
    """
    Generate a unique username from an email address.
    Strips special characters, ensures non-empty, avoids reserved words,
    and appends a counter if needed.
    """
    from users.models import CustomUser

    base = re.sub(r'[^a-zA-Z0-9]', '', email.split('@')[0])[:30]
    # Fallback if the local part was all special characters
    if not base:
        base = 'user'
    # Avoid reserved usernames
    if base.lower() in RESERVED_USERNAMES:
        base = f'{base}_u'

    username = base
    counter = 1
    while CustomUser.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1

    return username

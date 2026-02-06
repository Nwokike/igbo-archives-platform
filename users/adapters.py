from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed.
        """
        # If user is already logged in, let the default logic handle connecting the account
        if request.user.is_authenticated:
            return

        # If this social account is already connected to a user, let default logic handle login
        if sociallogin.is_existing:
            return

        # If not connected, check if we have a user with this email
        email = sociallogin.account.extra_data.get('email') or sociallogin.user.email
        
        if email:
            try:
                # Look for an existing user with this email (case-insensitive)
                user = User.objects.get(email__iexact=email)
                
                # If found, connect this new social account to the existing user
                sociallogin.connect(request, user)
                
            except User.DoesNotExist:
                # No existing user, proceed with standard signup
                pass

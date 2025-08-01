from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import UserAction

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    UserAction.objects.create(user=user, action_type='LOGIN')

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    UserAction.objects.create(user=user, action_type='LOGOUT')
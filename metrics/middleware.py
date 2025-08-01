from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .models import PageView

class RequestLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith(settings.STATIC_URL) or \
           request.path.startswith(settings.MEDIA_URL) or \
           request.path.startswith('/admin/'):
            return

        ip_address = request.META.get('REMOTE_ADDR')
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]

        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key

        PageView.objects.create(
            user=user,
            session_key=session_key,
            path=request.path,
            method=request.method,
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        return None
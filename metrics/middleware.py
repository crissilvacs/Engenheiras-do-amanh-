# metrics/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.utils import timezone
from .models import PageView
from datetime import timedelta

class RequestLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Exclua URLs estáticas e de admin
        if request.path.startswith(settings.STATIC_URL) or \
           request.path.startswith(settings.MEDIA_URL) or \
           request.path.startswith('/admin/'):
            return

        # Para que a lógica de "primeiro acesso" funcione, a sessão precisa de uma chave
        if not request.session.session_key:
            request.session.save()
            
        session_key = request.session.session_key

        # Verifica se já houve um PageView para esta sessão e caminho na última hora
        # Você pode ajustar este timedelta para o que preferir (ex: 1 dia)
        latest_pageview = PageView.objects.filter(
            session_key=session_key,
            path=request.path
        ).order_by('-timestamp').first()

        if latest_pageview and (timezone.now() - latest_pageview.timestamp) < timedelta(hours=1):
            return # Se já acessou na última hora, não registra de novo

        # Obtém o IP do cliente
        ip_address = request.META.get('REMOTE_ADDR')
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]

        user = request.user if request.user.is_authenticated else None

        PageView.objects.create(
            user=user,
            session_key=session_key,
            path=request.path,
            method=request.method,
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        return None
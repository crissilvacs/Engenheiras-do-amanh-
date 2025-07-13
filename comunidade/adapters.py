from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.models import User

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Este adaptador personaliza o comportamento do django-allauth para
    controlar os fluxos de login e registro social.
    """
    def pre_social_login(self, request, sociallogin):
        """
        Esta função é chamada logo antes de um login social ser finalizado.
        """
        # Pega o email do usuário retornado pelo Google
        email = sociallogin.user.email
        # Verifica se um usuário com este email já existe no nosso banco de dados
        user_exists = User.objects.filter(email=email).exists()

        # Pega o tipo de processo ('login' ou 'signup') da URL
        process = request.GET.get('process')

        # --- Lógica para a TELA DE LOGIN ---
        if process == 'login':
            # Se o usuário está tentando fazer login, mas a conta não existe...
            if not user_exists:
                # ...nós bloqueamos o processo.
                messages.error(request, "Esta conta não está cadastrada. Por favor, utilize a página de registro primeiro.")
                raise ImmediateHttpResponse(redirect('login'))

        # --- Lógica para a TELA DE CADASTRO ---
        if process == 'signup':
            # Se o usuário está tentando se cadastrar, mas a conta já existe...
            if user_exists:
                # ...nós bloqueamos o processo.
                messages.error(request, "Essa conta já possui cadastro. Por favor, faça o login.")
                raise ImmediateHttpResponse(redirect('login'))

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.contrib import messages
from django.shortcuts import redirect

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Este adaptador personaliza o comportamento do django-allauth.
    """
    def pre_social_login(self, request, sociallogin):
        """
        Esta função é chamada antes de um login social ser finalizado.
        """
        # Verificamos se o usuário veio do fluxo de 'signup'
        process = request.GET.get('process')

        # Se o usuário está tentando se CADASTRAR (signup)...
        if process == 'signup':
            # ...mas a conta social dele JÁ EXISTE no nosso sistema...
            if sociallogin.is_existing:
                # ...nós o impedimos de continuar.
                
                # 1. Criamos a mensagem de erro.
                messages.error(request, "Essa conta já possui cadastro. Por favor, faça o login.")
                
                # 2. Interrompemos o fluxo e o redirecionamos para a página de login.
                raise ImmediateHttpResponse(redirect('login'))

        # Para todos os outros casos (como um login normal), não fazemos nada.
        # O allauth continuará com seu comportamento padrão.

from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('home/', views.pagina_inicial, name='pagina_inicial'),
    path('esqueci-senha/', views.solicitar_redefinicao_senha, name='esqueci_senha'),
    path('logout/', views.logout_view, name='logout'),
    path('novo-post/', views.novo_post_view, name='novo_post'),
]

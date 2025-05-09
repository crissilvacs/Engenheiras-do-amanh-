from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('home/', views.pagina_inicial, name='pagina_inicial'),
    path('esqueci-senha/', views.solicitar_redefinicao_senha, name='esqueci_senha'),
    path('logout/', views.logout_view, name='logout'),
    path('novo-post/', views.novo_post_view, name='novo_post'),
    path('comentar/<int:post_id>/', views.comentar_post, name='comentar_post'),
    path('curtir/<int:post_id>/', views.curtir_post, name='curtir_post'),
    path('perfil/', views.perfil, name='perfil'),  # <- ESSENCIAL
    path('atualizar-foto/', views.atualizar_foto, name='atualizar_foto'),
]

from django.urls import path
from . import views
from .views import ranking_view

urlpatterns = [
    path('', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('home/', views.pagina_inicial, name='pagina_inicial'),
    path('esqueci-senha/', views.solicitar_redefinicao_senha, name='esqueci_senha'),
    path('logout/', views.logout_view, name='logout'),
    path('novo-post/', views.novo_post_view, name='novo_post'),
    path('comentar/<int:post_id>/', views.comentar_post, name='comentar_post'),
    path('curtir/<int:post_id>/', views.curtir_post, name='curtir_post'),
    path('perfil/', views.perfil, name='perfil'),
    path('editar-post/<int:post_id>/', views.editar_post, name='editar_post'),
    path('excluir-post/<int:post_id>/', views.excluir_post, name='excluir_post'),
    path('ranking/', ranking_view, name='ranking'),
    path('compartilhar/<int:post_id>/', views.compartilhar_post, name='compartilhar_post')
]

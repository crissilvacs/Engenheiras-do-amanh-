# metrics/urls.py
from django.urls import path
from . import views

app_name = 'metrics'
urlpatterns = [
    path('', views.metrics_dashboard, name='dashboard'),  # <<-- CORRIGIDO: O dashboard agora é a URL raiz do app
    path('export/csv/', views.export_metrics_csv, name='export_csv'),
]
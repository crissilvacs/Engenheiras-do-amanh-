# metrics/urls.py
from django.urls import path
from . import views

app_name = 'metrics'
urlpatterns = [
    path('dashboard/', views.metrics_dashboard, name='dashboard'),
    path('export/csv/', views.export_metrics_csv, name='export_csv'),
]
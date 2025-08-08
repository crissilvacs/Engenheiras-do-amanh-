# metrics/views.py
from django.shortcuts import render
from django.db.models import Count, F, Sum
from django.utils import timezone
from datetime import timedelta, datetime
import csv
from django.http import HttpResponse
from django.db.models.functions import TruncDate
from django.contrib.contenttypes.models import ContentType
import json

# Importar modelos do seu aplicativo 'comunidade' para a contagem total
from comunidade.models import Post, Curtida, Comentario, Perfil, User

from django.contrib.auth.decorators import login_required, user_passes_test
from .models import PageView, UserAction

def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def metrics_dashboard(request):
    hoje = timezone.now().date()
    data_inicio = hoje - timedelta(days=6)
    data_fim = hoje
    periodo_selecionado = '7dias'

    if request.GET.get('data_inicio') and request.GET.get('data_fim'):
        try:
            data_inicio = datetime.strptime(request.GET.get('data_inicio'), '%Y-%m-%d').date()
            data_fim = datetime.strptime(request.GET.get('data_fim'), '%Y-%m-%d').date()
            periodo_selecionado = 'custom'
        except (ValueError, TypeError):
            data_inicio = hoje - timedelta(days=6)
            data_fim = hoje
            periodo_selecionado = '7dias'
    else:
        periodo = request.GET.get('periodo', '7dias')
        if periodo == '30dias':
            data_inicio = hoje - timedelta(days=29)
            data_fim = hoje
            periodo_selecionado = '30dias'
        elif periodo == '7dias':
            data_inicio = hoje - timedelta(days=6)
            data_fim = hoje
            periodo_selecionado = '7dias'

    posts_periodo = Post.objects.filter(data_criacao__date__range=[data_inicio, data_fim]).count()
    likes_periodo = Curtida.objects.filter(data__date__range=[data_inicio, data_fim]).count()
    comments_periodo = Comentario.objects.filter(data__date__range=[data_inicio, data_fim]).count()
    pageviews_periodo = PageView.objects.filter(timestamp__date__range=[data_inicio, data_fim]).count()

    total_posts_geral = Post.objects.count()
    total_likes_geral = Curtida.objects.count()
    total_comments_geral = Comentario.objects.count()
    total_pageviews_geral = PageView.objects.count()
    total_users_geral = User.objects.count()
    users_periodo = User.objects.filter(date_joined__date__range=[data_inicio, data_fim]).count()

    actions_query = UserAction.objects.filter(timestamp__date__range=[data_inicio, data_fim])
    pageviews_query = PageView.objects.filter(timestamp__date__range=[data_inicio, data_fim])

    pageviews_por_dia = pageviews_query.annotate(date=TruncDate('timestamp')).values('date').annotate(count=Count('date')).order_by('date')
    actions_por_tipo = actions_query.values('action_type').annotate(count=Count('action_type')).order_by('-count')

    pageviews_labels = [p['date'].strftime('%d/%b') for p in pageviews_por_dia]
    pageviews_data = [p['count'] for p in pageviews_por_dia]
    actions_labels = [a['action_type'] for a in actions_por_tipo]
    actions_data = [a['count'] for a in actions_por_tipo]

    recent_pageviews = pageviews_query.order_by('-timestamp')[:50]
    recent_actions = actions_query.order_by('-timestamp')[:50]

    context = {
        'posts_card': posts_periodo,
        'likes_card': likes_periodo,
        'comments_card': comments_periodo,
        'pageviews_card': pageviews_periodo,
        'users_card': users_periodo,

        'total_posts_geral': total_posts_geral,
        'total_likes_geral': total_likes_geral,
        'total_comments_geral': total_comments_geral,
        'total_pageviews_geral': total_pageviews_geral,
        'total_users_geral': total_users_geral,
        
        'pageviews_labels_json': json.dumps(pageviews_labels),
        'pageviews_data_json': json.dumps(pageviews_data),
        'actions_labels_json': json.dumps(actions_labels),
        'actions_data_json': json.dumps(actions_data),

        'recent_pageviews': recent_pageviews,
        'recent_actions': recent_actions,

        'data_inicio': data_inicio.strftime('%Y-%m-%d'),
        'data_fim': data_fim.strftime('%Y-%m-%d'),
        'periodo_selecionado': periodo_selecionado,
    }
    return render(request, 'metrics/dashboard.html', context)

@login_required
@user_passes_test(is_superuser)
def export_metrics_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="metricas_uso_{timezone.now().date()}.csv"'

    writer = csv.writer(response)

    writer.writerow(['Métrica', 'Total', 'Hoje'])

    total_pageviews = PageView.objects.count()
    pageviews_today = PageView.objects.filter(timestamp__date=timezone.now().date()).count()
    writer.writerow(['Acessos (Page Views)', total_pageviews, pageviews_today])

    total_posts = UserAction.objects.filter(action_type='POST_CRIADO').count()
    posts_today = UserAction.objects.filter(action_type='POST_CRIADO', timestamp__date=timezone.now().date()).count()
    writer.writerow(['Posts Novos', total_posts, posts_today])

    total_likes = UserAction.objects.filter(action_type='CURTIDA_CRIADA').count()
    likes_today = UserAction.objects.filter(action_type='CURTIDA_CRIADA', timestamp__date=timezone.now().date()).count()
    writer.writerow(['Curtidas', total_likes, likes_today])

    total_comments = UserAction.objects.filter(action_type='COMENTARIO_CRIADO').count()
    comments_today = UserAction.objects.filter(action_type='COMENTARIO_CRIADO', timestamp__date=timezone.now().date()).count()
    writer.writerow(['Comentários', total_comments, comments_today])

    return response
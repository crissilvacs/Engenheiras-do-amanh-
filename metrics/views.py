# metrics/views.py
from django.shortcuts import render
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta, datetime
import csv
import json
from django.http import HttpResponse
from django.db.models.functions import TruncDate
from django.contrib.auth.decorators import login_required, user_passes_test

# Modelos do app comunidade
from comunidade.models import Post, Curtida, Comentario, Perfil, User

# Modelos do app metrics
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

    # Período customizado
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
        else:
            data_inicio = hoje - timedelta(days=6)
            data_fim = hoje
            periodo_selecionado = '7dias'

    # Contagens do período
    posts_periodo = Post.objects.filter(data_criacao__date__range=[data_inicio, data_fim]).count()
    likes_periodo = Curtida.objects.filter(data__date__range=[data_inicio, data_fim]).count()
    comments_periodo = Comentario.objects.filter(data__date__range=[data_inicio, data_fim]).count()

    # ACESSOS = LOGINS (correção principal)
    logins_periodo = UserAction.objects.filter(
        action_type='LOGIN',
        timestamp__date__range=[data_inicio, data_fim]
    ).count()

    # Totais gerais
    total_posts_geral = Post.objects.count()
    total_likes_geral = Curtida.objects.count()
    total_comments_geral = Comentario.objects.count()
    total_logins_geral = UserAction.objects.filter(action_type='LOGIN').count()
    total_users_geral = User.objects.count()
    users_periodo = User.objects.filter(date_joined__date__range=[data_inicio, data_fim]).count()

    # Consultas base
    actions_query = UserAction.objects.filter(timestamp__date__range=[data_inicio, data_fim])
    logins_query = actions_query.filter(action_type='LOGIN')
    pageviews_query = PageView.objects.filter(timestamp__date__range=[data_inicio, data_fim])  # mantido para a tabela

    # Séries para os gráficos
    # (Acessos por Dia = LOGINS por dia)
    logins_por_dia = (
        logins_query
        .annotate(date=TruncDate('timestamp'))
        .values('date').annotate(count=Count('date')).order_by('date')
    )
    actions_por_tipo = (
        actions_query
        .values('action_type').annotate(count=Count('action_type'))
        .order_by('-count')
    )

    # Mantemos os nomes esperados pelo template:
    pageviews_labels = [p['date'].strftime('%d/%b') for p in logins_por_dia]
    pageviews_data = [p['count'] for p in logins_por_dia]
    actions_labels = [a['action_type'] for a in actions_por_tipo]
    actions_data = [a['count'] for a in actions_por_tipo]

    # Prévia para o CSV (Acessos = LOGINS)
    logins_csv_data = logins_por_dia  # já agrupado por dia

    posts_csv_data = (
        Post.objects.filter(data_criacao__date__range=[data_inicio, data_fim])
        .annotate(date=TruncDate('data_criacao'))
        .values('date').annotate(count=Count('date')).order_by('date')
    )
    likes_csv_data = (
        Curtida.objects.filter(data__date__range=[data_inicio, data_fim])
        .annotate(date=TruncDate('data'))
        .values('date').annotate(count=Count('date')).order_by('date')
    )
    comments_csv_data = (
        Comentario.objects.filter(data__date__range=[data_inicio, data_fim])
        .annotate(date=TruncDate('data'))
        .values('date').annotate(count=Count('date')).order_by('date')
    )

    acessos_dict = {p['date']: p['count'] for p in logins_csv_data}
    posts_dict = {p['date']: p['count'] for p in posts_csv_data}
    likes_dict = {p['date']: p['count'] for p in likes_csv_data}
    comments_dict = {p['date']: p['count'] for p in comments_csv_data}

    dias = [data_inicio + timedelta(days=d) for d in range((data_fim - data_inicio).days + 1)]
    csv_preview_data = []
    for dia in dias:
        csv_preview_data.append({
            'Data': dia.strftime('%Y-%m-%d'),
            'Acessos': acessos_dict.get(dia, 0),
            'Posts': posts_dict.get(dia, 0),
            'Curtidas': likes_dict.get(dia, 0),
            'Comentários': comments_dict.get(dia, 0),
        })

    # Listas “Recentes” (mantidas)
    recent_pageviews = pageviews_query.order_by('-timestamp')[:50]
    recent_actions = actions_query.order_by('-timestamp')[:50]

    context = {
        'posts_card': posts_periodo,
        'likes_card': likes_periodo,
        'comments_card': comments_periodo,
        # Card "Acessos" agora mostra logins
        'pageviews_card': logins_periodo,
        'users_card': users_periodo,

        'total_posts_geral': total_posts_geral,
        'total_likes_geral': total_likes_geral,
        'total_comments_geral': total_comments_geral,
        # Total de “Acessos” = total de logins
        'total_pageviews_geral': total_logins_geral,
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
        'csv_preview_data': csv_preview_data,
    }
    return render(request, 'metrics/dashboard.html', context)


@login_required
@user_passes_test(is_superuser)
def export_metrics_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="metricas_diarias_{timezone.now().date()}.csv"'
    writer = csv.writer(response)

    # Cabeçalho
    writer.writerow(['Data', 'Acessos', 'Posts', 'Curtidas', 'Comentários'])

    # Período
    hoje = timezone.now().date()
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')

    if data_inicio_str and data_fim_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            data_inicio = hoje - timedelta(days=6)
            data_fim = hoje
    else:
        data_inicio = hoje - timedelta(days=6)
        data_fim = hoje

    # Agrupamentos por dia (Acessos = LOGINS)
    logins_por_dia = (
        UserAction.objects.filter(action_type='LOGIN', timestamp__date__range=[data_inicio, data_fim])
        .annotate(date=TruncDate('timestamp'))
        .values('date').annotate(count=Count('date')).order_by('date')
    )
    posts_por_dia = (
        Post.objects.filter(data_criacao__date__range=[data_inicio, data_fim])
        .annotate(date=TruncDate('data_criacao'))
        .values('date').annotate(count=Count('date')).order_by('date')
    )
    likes_por_dia = (
        Curtida.objects.filter(data__date__range=[data_inicio, data_fim])
        .annotate(date=TruncDate('data'))
        .values('date').annotate(count=Count('date')).order_by('date')
    )
    comments_por_dia = (
        Comentario.objects.filter(data__date__range=[data_inicio, data_fim])
        .annotate(date=TruncDate('data'))
        .values('date').annotate(count=Count('date')).order_by('date')
    )

    acessos_dict = {p['date']: p['count'] for p in logins_por_dia}
    posts_dict = {p['date']: p['count'] for p in posts_por_dia}
    likes_dict = {p['date']: p['count'] for p in likes_por_dia}
    comments_dict = {p['date']: p['count'] for p in comments_por_dia}

    dias = [data_inicio + timedelta(days=d) for d in range((data_fim - data_inicio).days + 1)]
    for dia in dias:
        dia_str = dia.strftime('%Y-%m-%d')
        writer.writerow([
            dia_str,
            acessos_dict.get(dia, 0),
            posts_dict.get(dia, 0),
            likes_dict.get(dia, 0),
            comments_dict.get(dia, 0),
        ])

    return response

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.db.models import Q, F, Prefetch
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Post, Comentario, Curtida, Perfil, User
from .forms import RegistroForm, LoginForm, PerfilForm, PostForm
from metrics.models import UserAction

# --- PONTUAÇÃO CENTRALIZADA ---
# Ações Ativas
PONTOS_NOVO_POST = 15
PONTOS_COMENTARIO = 4
PONTOS_COMPARTILHAMENTO = 5
PONTOS_CURTIDA = 1
BONUS_DIARIO = 10
LIMITE_CURTIDAS_DIARIAS = 10

# Recompensas de Engajamento (para a autora do post)
PONTOS_RECEBER_COMENTARIO = 4
PONTOS_RECEBER_CURTIDA = 2
PONTOS_RECEBER_COMPARTILHAMENTO = 3

def gerenciar_pontos(user, tipo_acao, post_autor=None):
    """
    Função central para gerir toda a lógica de pontuação.
    'user' é quem realiza a ação.
    'post_autor' é o autor do post que está a receber a interação.
    """
    # Pontos para quem realiza a ação (o "ator")
    if user:
        perfil_ator, _ = Perfil.objects.get_or_create(user=user)
        hoje = timezone.now().date()
        pontos_adicionados_ator = 0
        
        # 1. Verifica e aplica o bónus diário para o ator
        if perfil_ator.ultima_interacao != hoje:
            pontos_adicionados_ator += BONUS_DIARIO
            perfil_ator.ultima_interacao = hoje

        # 2. Aplica a pontuação da ação específica
        if tipo_acao == 'post':
            pontos_adicionados_ator += PONTOS_NOVO_POST
        elif tipo_acao == 'comentario':
            pontos_adicionados_ator += PONTOS_COMENTARIO
        elif tipo_acao == 'curtida':
            pontos_adicionados_ator += PONTOS_CURTIDA
        elif tipo_acao == 'compartilhamento':
            pontos_adicionados_ator += PONTOS_COMPARTILHAMENTO

        # 3. Atualiza os pontos do perfil do ator
        if pontos_adicionados_ator > 0:
            perfil_ator.pontos = F('pontos') + pontos_adicionados_ator
            perfil_ator.save()

    # 4. Pontos para a autora do post (se aplicável e se não for a mesma pessoa)
    if post_autor and post_autor != user:
        perfil_autor, _ = Perfil.objects.get_or_create(user=post_autor)
        pontos_adicionados_autor = 0
        if tipo_acao == 'comentario':
            pontos_adicionados_autor += PONTOS_RECEBER_COMENTARIO
        elif tipo_acao == 'curtida':
            pontos_adicionados_autor += PONTOS_RECEBER_CURTIDA
        elif tipo_acao == 'compartilhamento':
            pontos_adicionados_autor += PONTOS_RECEBER_COMPARTILHAMENTO
        
        if pontos_adicionados_autor > 0:
            perfil_autor.pontos = F('pontos') + pontos_adicionados_autor
            perfil_autor.save()


# --- VIEWS PRINCIPAIS E DE GAMIFICAÇÃO ---

from django.db.models import Q, F, Prefetch, Count  # Count aqui

@login_required
def pagina_inicial(request):
    query = request.GET.get('q', '')

    qs = (
        Post.objects
        .select_related('autor__perfil')
        .prefetch_related(
            'tags',
            'curtidas',
            Prefetch(
                'comentarios',
                queryset=Comentario.objects.select_related('autor__perfil').order_by('-data')
            )
        )
        .annotate(
            num_comentarios=Count('comentarios', distinct=True),
            num_curtidas=Count('curtidas', distinct=True),
        )
        .order_by('-data_criacao')
    )

    if query:
        qs = qs.filter(
            Q(titulo__icontains=query) |
            Q(conteudo__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    from django.core.paginator import Paginator, EmptyPage
    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')

    try:
        posts = paginator.page(page_number)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    except:
        posts = paginator.page(1)

    perfil, _ = Perfil.objects.get_or_create(user=request.user)

    # >>> AQUI: ids dos posts da página que o usuário já curtiu
    page_post_ids = list(posts.object_list.values_list('id', flat=True))
    liked_post_ids = list(
        Curtida.objects.filter(usuario=request.user, post_id__in=page_post_ids)
        .values_list('post_id', flat=True)
    )

    return render(request, 'comunidade/pagina_inicial.html', {
        'posts': posts,
        'perfil': perfil,
        'liked_post_ids': liked_post_ids,  # usado no template para pintar o coração
    })


@login_required
def novo_post_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.autor = request.user
            post.save()
            form.save_m2m()
            gerenciar_pontos(request.user, 'post')
            return redirect('pagina_inicial')
    else:
        form = PostForm()
    perfil, _ = Perfil.objects.get_or_create(user=request.user)
    return render(request, 'comunidade/novo_post.html', {'perfil': perfil, 'form': form})

@login_required
def comentar_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        texto = request.POST.get('comentario')
        if texto:
            # Limite: A pontuação (para ambos) só é dada no primeiro comentário de um utilizador num post.
            if not Comentario.objects.filter(post=post, autor=request.user).exists():
                gerenciar_pontos(request.user, 'comentario', post_autor=post.autor)
            
            novo_comentario = Comentario.objects.create(post=post, autor=request.user, texto=texto)
            UserAction.objects.create(user=request.user, action_type='COMENTARIO_CRIADO', content_object=novo_comentario)

    return HttpResponseRedirect(f"{reverse('pagina_inicial')}#post-{post.id}")

@login_required
def curtir_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    curtida, created = Curtida.objects.get_or_create(post=post, usuario=request.user)

    if created:
        # Limite para quem curte: Ganha pontos apenas nas 10 primeiras curtidas do dia
        curtidas_hoje = Curtida.objects.filter(usuario=request.user, data__date=timezone.now().date()).count()
        if curtidas_hoje <= LIMITE_CURTIDAS_DIARIAS:
            gerenciar_pontos(request.user, 'curtida', post_autor=post.autor)
        else:
            # Se o limite de curtidas diárias foi atingido, só a autora ganha pontos
            gerenciar_pontos(None, 'curtida', post_autor=post.autor)
    else:
        curtida.delete()
        # Lógica para remover pontos (opcional)
        
    return HttpResponseRedirect(f"{reverse('pagina_inicial')}#post-{post.id}")

@login_required
def compartilhar_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    gerenciar_pontos(request.user, 'compartilhamento', post_autor=post.autor)
    return redirect('pagina_inicial')


# --- VIEWS DE AUTENTICAÇÃO E PERFIL ---

def login_view(request):
    if request.user.is_authenticated:
        return redirect('pagina_inicial')
    erro = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['username']
            senha = form.cleaned_data['password']
            user = authenticate(request, username=email, password=senha)
            if user:
                login(request, user)
                return redirect('pagina_inicial')
            else:
                erro = 'Credenciais inválidas. Por favor, tente novamente.'
    else:
        form = LoginForm()
    return render(request, 'comunidade/login.html', {'form': form, 'erro': erro})

def registro_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            nome = form.cleaned_data['nome']
            email = form.cleaned_data['email']
            senha = form.cleaned_data['senha']
            telefone = form.cleaned_data['telefone']
            if User.objects.filter(username=email).exists():
                return render(request, 'comunidade/register.html', {'form': form, 'erro': 'Este e-mail já está em uso.'})
            user = User.objects.create_user(username=email, email=email, password=senha, first_name=nome)
            Perfil.objects.create(user=user, telefone=telefone)
            return render(request, 'comunidade/register.html', {'form': RegistroForm(), 'show_success_modal': True})
    else:
        form = RegistroForm()
    return render(request, 'comunidade/register.html', {'form': form})

def logout_view(request):
    logout(request)
    # tenta usar ?next= ou input hidden; se não tiver, vai pra 'welcome'
    next_url = request.POST.get('next') or request.GET.get('next')
    return redirect(next_url or 'welcome')

@login_required
def perfil_view(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)
    posts = Post.objects.filter(autor=request.user).order_by('-data_criacao')
    context = {
        'perfil': perfil,
        'posts': posts,
        'posts_qtd': posts.count(),
        'curtidas_qtd': Curtida.objects.filter(usuario=request.user).count(),
        'comentarios_qtd': Comentario.objects.filter(autor=request.user).count(),
    }
    return render(request, 'comunidade/perfil.html', context)

@login_required
def editar_perfil(request):
    perfil = get_object_or_404(Perfil, user=request.user)
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('nome', user.first_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        perfil.telefone = request.POST.get('telefone', perfil.telefone)
        if 'foto' in request.FILES:
            perfil.foto = request.FILES['foto']
        perfil.save()
        return redirect('perfil')
    return render(request, 'comunidade/editar_perfil.html', {'perfil': perfil})

@login_required
def editar_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, autor=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('perfil')
    else:
        form = PostForm(instance=post)
    return render(request, 'comunidade/editar_post.html', {'post': post, 'form': form})

@login_required
def excluir_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, autor=request.user)
    if request.method == 'POST':
        post.delete()
        return redirect('perfil')
    return render(request, 'comunidade/excluir_post.html', {'post': post})

def ranking_view(request):
    perfis = Perfil.objects.select_related('user').order_by('-pontos')
    context = {
        'podio': perfis[:3],
        'restantes': perfis[3:],
    }
    return render(request, 'comunidade/ranking.html', context)

# Você pode remover esta view se não estiver mais usando o modal de tags
@login_required
def visualizar_tags(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return render(request, 'comunidade/modal_tags.html', {'tags': post.tags.all()})

# Simulações de redefinição de senha (podem ser removidas se não estiverem em uso)
def solicitar_redefinicao_senha(request):
    return redirect('login')

def redefinir_senha(request):
    return redirect('login')

def stema_welcome(request):
    # Se já estiver logada, pula a welcome e vai pra home
    if request.user.is_authenticated:
        return redirect('pagina_inicial')
    return render(request, 'comunidade/welcome.html')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.db.models import Q, F
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Post, Comentario, Curtida, Perfil, User
from .forms import RegistroForm, LoginForm, PerfilForm, PostForm
from django.contrib import messages

# --- PONTUAÇÃO CENTRALIZADA ---
PONTOS_NOVO_POST = 15
PONTOS_COMENTARIO = 10
PONTOS_COMPARTILHAMENTO = 5
PONTOS_CURTIDA = 1
BONUS_DIARIO = 10
LIMITE_CURTIDAS_DIARIAS = 10

def gerenciar_pontos(user, tipo_acao):
    """
    Função central para gerenciar toda a lógica de pontuação.
    """
    perfil, _ = Perfil.objects.get_or_create(user=user)
    hoje = timezone.now().date()
    pontos_adicionados = 0
    
    # 1. Verifica e aplica o bônus diário
    if perfil.ultima_interacao != hoje:
        pontos_adicionados += BONUS_DIARIO
        perfil.ultima_interacao = hoje

    # 2. Aplica a pontuação da ação específica
    if tipo_acao == 'post':
        pontos_adicionados += PONTOS_NOVO_POST
    elif tipo_acao == 'comentario':
        pontos_adicionados += PONTOS_COMENTARIO
    elif tipo_acao == 'curtida':
        pontos_adicionados += PONTOS_CURTIDA
    elif tipo_acao == 'compartilhamento':
        pontos_adicionados += PONTOS_COMPARTILHAMENTO

    # 3. Atualiza os pontos do perfil de forma segura
    if pontos_adicionados > 0:
        perfil.pontos = F('pontos') + pontos_adicionados
        perfil.save()

# --- VIEWS PRINCIPAIS E DE GAMIFICAÇÃO ---

@login_required
def pagina_inicial(request):
    query = request.GET.get('q', '')
    
    if query:
        posts = Post.objects.filter(
            Q(titulo__icontains=query) |
            Q(conteudo__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct().prefetch_related('tags').order_by('-data_criacao')
    else:
        posts = Post.objects.all().prefetch_related('tags').order_by('-data_criacao')
    
    perfil, created = Perfil.objects.get_or_create(user=request.user)
    
    return render(request, 'comunidade/pagina_inicial.html', {
        'posts': posts,
        'perfil': perfil,
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
            # Limite: Ganha pontos apenas no primeiro comentário em um post
            if not Comentario.objects.filter(post=post, autor=request.user).exists():
                gerenciar_pontos(request.user, 'comentario')
            Comentario.objects.create(post=post, autor=request.user, texto=texto)
    return HttpResponseRedirect(f"{reverse('pagina_inicial')}#post-{post.id}")

@login_required
def curtir_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    curtida, created = Curtida.objects.get_or_create(post=post, usuario=request.user)

    if created:
        # Limite: Ganha pontos apenas nas 10 primeiras curtidas do dia
        curtidas_hoje = Curtida.objects.filter(usuario=request.user, data__date=timezone.now().date()).count()
        if curtidas_hoje <= LIMITE_CURTIDAS_DIARIAS:
            gerenciar_pontos(request.user, 'curtida')
    else:
        curtida.delete()
        
    return HttpResponseRedirect(f"{reverse('pagina_inicial')}#post-{post.id}")

@login_required
def compartilhar_post(request, post_id):
    gerenciar_pontos(request.user, 'compartilhamento')
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
            
            try:
                user = User.objects.create_user(username=email, email=email, password=senha, first_name=nome)
                Perfil.objects.create(user=user, telefone=telefone)
                messages.success(request, 'Cadastro realizado com sucesso! Faça login para continuar.')
                form = RegistroForm()
                return render(request, 'comunidade/register.html', {'form': form})
            except Exception as e:
                    messages.error(request, f'Ocorreu um erro inesperado ao cadastrar: {e}')
                    return render(request, 'comunidade/register.html', {'form': form})
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
            return render(request, 'comunidade/register.html', {'form': form})
    else:
        form = RegistroForm()
    return render(request, 'comunidade/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

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

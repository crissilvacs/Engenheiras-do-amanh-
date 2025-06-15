from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Post, Comentario, Curtida, Perfil
from .forms import RegistroForm

# Página inicial com listagem e busca de posts
@login_required
def pagina_inicial(request):
    query = request.GET.get('q', '')
    
    # OTIMIZAÇÃO: Adicionar prefetch_related para tags
    if query:
        posts = Post.objects.filter(
            Q(titulo__icontains=query) |
            Q(conteudo__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct().prefetch_related('tags').order_by('-data_criacao')
    else:
        posts = Post.objects.all().prefetch_related('tags').order_by('-data_criacao')
    
    perfil = get_object_or_404(Perfil, user=request.user)
    
    return render(request, 'comunidade/pagina_inicial.html', {
        'posts': posts,
        'perfil': perfil,
    })

@login_required
def visualizar_tags(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    tags = post.tags.all()
    return render(request, 'comunidade/modal_tags.html', {'tags': tags})

# Autenticação do usuário
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')
        senha = request.POST.get('password')
        user = authenticate(request, username=email, password=senha)
        if user:
            login(request, user)
            perfil, _ = Perfil.objects.get_or_create(user=user)
            perfil.pontos += 10
            perfil.save()
            return redirect('pagina_inicial')
        return render(request, 'comunidade/login.html', {'erro': 'Credenciais inválidas.'})
    return render(request, 'comunidade/login.html')

# Logout do usuário
def logout_view(request):
    logout(request)
    return redirect('login')

# Registro de novo usuário
def registro_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            nome = form.cleaned_data['nome']
            email = form.cleaned_data['email']
            senha = form.cleaned_data['senha']
            telefone = form.cleaned_data['telefone']

            if User.objects.filter(username=email).exists():
                return render(request, 'comunidade/register.html', {
                    'form': form,
                    'erro': 'Este e-mail já está em uso.'
                })

            user = User.objects.create_user(
                username=email,
                email=email,
                password=senha,
                first_name=nome
            )
            user.save()

            perfil = Perfil.objects.create(user=user, telefone=telefone)
            perfil.save()

            return redirect('login')
    else:
        form = RegistroForm()

    return render(request, 'comunidade/register.html', {'form': form})

# Solicitação de redefinição de senha (simulado)
def solicitar_redefinicao_senha(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        print(f"[DEBUG] Requisição de redefinição de senha para: {email}")
        return redirect('redefinir_senha')
    return render(request, 'comunidade/nova_senha.html')

# Redefinir senha (simulado)
def redefinir_senha(request):
    if request.method == 'POST':
        nova_senha = request.POST.get('new_password1')
        confirmar_senha = request.POST.get('new_password2')
        if nova_senha == confirmar_senha:
            print("[DEBUG] Senha redefinida com sucesso!")
            return redirect('login')
        return render(request, 'comunidade/recuperar_senha.html', {
            'erro': 'As senhas não coincidem.'
        })
    return render(request, 'comunidade/recuperar_senha.html')

# Criar novo post
from .forms import PostForm

@login_required
def novo_post_view(request):
    perfil = get_object_or_404(Perfil, user=request.user)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.autor = request.user
            post.save()
            form.save_m2m()  # ESSENCIAL para ManyToMany como as tags
            perfil.pontos += 10
            perfil.save()
            return redirect('pagina_inicial')
    else:
        form = PostForm()

    return render(request, 'comunidade/novo_post.html', {'perfil': perfil, 'form': form})


# Comentar em um post
@login_required
def comentar_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        texto = request.POST.get('comentario')
        if texto:
            Comentario.objects.create(post=post, autor=request.user, texto=texto)
            perfil, _ = Perfil.objects.get_or_create(user=request.user)
            perfil.pontos += 3 
            perfil.save()
    return HttpResponseRedirect(f"{reverse('pagina_inicial')}#post-{post.id}")

# Curtir ou descurtir um post
@login_required
def curtir_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    curtida, created = Curtida.objects.get_or_create(post=post, usuario=request.user)
    perfil, _ = Perfil.objects.get_or_create(user=request.user)

    if created:
        perfil.pontos += 5
    
    if not created:
        curtida.delete()
        perfil.pontos -= 5

    perfil.save()
    return HttpResponseRedirect(f"{reverse('pagina_inicial')}#post-{post.id}")

@login_required
def compartilhar_post(request, post_id):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)
    perfil.pontos += 2 
    perfil.save()
    return redirect('pagina_inicial')

# Perfil do usuário
@login_required
def perfil(request):
    user = request.user
    perfil, _ = Perfil.objects.get_or_create(user=user)

    if request.method == 'POST':
        user.first_name = request.POST.get('nome')
        user.email = request.POST.get('email')
        user.save()

        perfil.telefone = request.POST.get('telefone')
        if 'foto' in request.FILES:
            perfil.foto = request.FILES['foto']
        perfil.save()

        return redirect('perfil')

    posts_qtd = Post.objects.filter(autor=user).count()
    curtidas_qtd = Curtida.objects.filter(usuario=user).count()
    comentarios_qtd = Comentario.objects.filter(autor=user).count()
    posts = Post.objects.filter(autor=user).order_by('-data_criacao')

    context = {
        'user': user,
        'perfil': perfil,
        'posts_qtd': posts_qtd,
        'curtidas_qtd': curtidas_qtd,
        'comentarios_qtd': comentarios_qtd,
        'posts': posts
    }
    return render(request, 'comunidade/perfil.html', context)

@login_required
def editar_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, autor=request.user)

    if request.method == 'POST':
        post.titulo = request.POST.get('titulo')
        post.conteudo = request.POST.get('conteudo')
        if 'anexo' in request.FILES:
            post.imagem = request.FILES['anexo']
        post.save()
        return redirect('perfil')

    return render(request, 'comunidade/editar_post.html', {'post': post})

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post

@login_required
def excluir_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, autor=request.user)

    if request.method == 'POST':
        post.delete()
        return redirect('perfil')

    return render(request, 'comunidade/excluir_post.html', {'post': post})

def ranking_view(request):
    perfis = Perfil.objects.select_related('user').order_by('-pontos')

    podio = perfis[:3]
    restantes = perfis[3:]

    context = {
        'podio': podio,
        'restantes': restantes,
    }
    return render(request, 'comunidade/ranking.html', context)
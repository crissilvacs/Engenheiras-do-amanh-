from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Post, Comentario, Curtida, Perfil

# Página inicial com listagem e busca de posts
@login_required
def pagina_inicial(request):
    # busca os posts...
    posts = Post.objects.all().order_by('-data_criacao')

    # busca o perfil do usuário logado
    perfil = get_object_or_404(Perfil, user=request.user)

    return render(request, 'comunidade/pagina_inicial.html', {
        'posts': posts,
        'perfil': perfil,
    })

# Autenticação do usuário
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')
        senha = request.POST.get('password')
        user = authenticate(request, username=email, password=senha)
        if user:
            login(request, user)
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
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        telefone = request.POST.get('telefone')

        if User.objects.filter(username=email).exists():
            return render(request, 'comunidade/register.html', {
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

    return render(request, 'comunidade/register.html')

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
@login_required
def novo_post_view(request):
    # Certifica-se de buscar o perfil do usuário logado
    perfil = get_object_or_404(Perfil, user=request.user)

    if request.method == 'POST':
        titulo   = request.POST.get('titulo')
        conteudo = request.POST.get('conteudo')
        imagem   = request.FILES.get('anexo')
        Post.objects.create(
            titulo       = titulo,
            conteudo     = conteudo,
            imagem       = imagem,
            autor        = request.user,
            data_criacao = timezone.now()
        )
        return redirect('pagina_inicial')

    # Passa o perfil ao template
    return render(request, 'comunidade/novo_post.html', {
        'perfil': perfil
    })

# Comentar em um post
@login_required
def comentar_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        texto = request.POST.get('comentario')
        if texto:
            Comentario.objects.create(post=post, autor=request.user, texto=texto)
    return HttpResponseRedirect(f"{reverse('pagina_inicial')}#post-{post.id}")

# Curtir ou descurtir um post
@login_required
def curtir_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    curtida, created = Curtida.objects.get_or_create(post=post, usuario=request.user)
    if not created:
        curtida.delete()
    return HttpResponseRedirect(f"{reverse('pagina_inicial')}#post-{post.id}")

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


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Post
from django.utils import timezone
from django.db.models import Q

# Página inicial com os posts (acesso apenas autenticado)
@login_required(login_url='login')
def pagina_inicial(request):
    query = request.GET.get('q')
    if query:
        posts = Post.objects.filter(
            Q(titulo__icontains=query) |
            Q(conteudo__icontains=query)
        )
    else:
        posts = Post.objects.all().order_by('-data_criacao')
    return render(request, 'comunidade/pagina_inicial.html', {'posts': posts})


# View de login
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')
        senha = request.POST.get('password')

        user = authenticate(request, username=email, password=senha)
        if user:
            login(request, user)
            return redirect('pagina_inicial')
        else:
            return render(request, 'comunidade/login.html', {'erro': 'Credenciais inválidas'})
    
    return render(request, 'comunidade/login.html')


# View de logout
def logout_view(request):
    logout(request)
    return redirect('login')


# View de registro
def registro_view(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        telefone = request.POST.get('telefone')

        # Verifica se o e-mail já está cadastrado
        if User.objects.filter(username=email).exists():
            erro = 'Este e-mail já está em uso.'
            return render(request, 'comunidade/register.html', {'erro': erro})

        # Cria usuário
        user = User.objects.create_user(username=email, email=email, password=senha, first_name=nome)
        user.save()

        return redirect('login')

    return render(request, 'comunidade/register.html')


# View da solicitação de redefinição de senha
def solicitar_redefinicao_senha(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        print(f"[DEBUG] Requisição de redefinição de senha para: {email}")
        return redirect('redefinir_senha')  # Simulação

    return render(request, 'comunidade/nova_senha.html')


# View para redefinir a nova senha
def redefinir_senha(request):
    if request.method == 'POST':
        nova_senha = request.POST.get('new_password1')
        confirmar_senha = request.POST.get('new_password2')

        if nova_senha == confirmar_senha:
            print("[DEBUG] Senha redefinida com sucesso!")
            return redirect('login')
        else:
            return render(request, 'comunidade/recuperar_senha.html', {
                'erro': 'As senhas não coincidem.'
            })

    return render(request, 'comunidade/recuperar_senha.html')

@login_required
def novo_post_view(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        conteudo = request.POST.get('conteudo')
        imagem = request.FILES.get('anexo')
        autor = request.user 

        Post.objects.create(
            titulo=titulo,
            conteudo=conteudo,
            imagem=imagem,
            autor=autor,
            data_criacao=timezone.now()
        )
        return redirect('pagina_inicial')

    return render(request, 'comunidade/novo_post.html')
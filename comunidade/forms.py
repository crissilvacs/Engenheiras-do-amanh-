from django import forms
from django.contrib.auth.models import User
from captcha.fields import CaptchaField
from taggit.forms import TagWidget
from .models import Post, Perfil

# --- Formulários de Autenticação ---

class RegistroForm(forms.Form):
    nome = forms.CharField(label="Nome completo", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    senha = forms.CharField(label="Senha", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    telefone = forms.CharField(label="Telefone", max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    captcha = CaptchaField(label="Verificação")


class LoginForm(forms.Form):
    """
    Novo formulário de login com campo de e-mail, senha e captcha.
    """
    username = forms.EmailField(
        label="E-mail",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'id': 'email', 'autocomplete': 'username'})
    )
    password = forms.CharField(
        label="Senha",
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'senha', 'autocomplete': 'current-password'})
    )
    # Label removido para não aparecer no formulário
    captcha = CaptchaField(label="")


# --- Formulário de Post ---

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['titulo', 'conteudo', 'imagem', 'tags']
        tags = forms.CharField(
        required=False, 
        widget=TagWidget(attrs={'class': 'form-control', 'placeholder': 'Separe as tags por vírgulas'})
    )


# --- Formulário de Perfil ---

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['foto', 'telefone']
        widgets = {
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

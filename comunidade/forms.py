from django import forms
from django.contrib.auth.models import User
from captcha.fields import CaptchaField


class RegistroForm(forms.Form):
    nome = forms.CharField(label="Nome completo", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    senha = forms.CharField(label="Senha", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    telefone = forms.CharField(label="Telefone", max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    captcha = CaptchaField()

from .models import Post
from taggit.forms import TagWidget

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['titulo', 'conteudo', 'imagem', 'tags']  # Inclua as tags
        widgets = {
            'tags': TagWidget(attrs={'class': 'form-control', 'placeholder': 'Separe as tags por vírgulas'}),
        }
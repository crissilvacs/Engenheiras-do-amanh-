from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['titulo', 'conteudo', 'tags']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control rounded-pill bg-light'}),
            'conteudo': forms.Textarea(attrs={'class': 'form-control bg-light', 'rows': 4}),
        }

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Post, Comentario, Curtida, Perfil

# Esta classe define como o Perfil será exibido DENTRO da página do Usuário
class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil do Usuário'
    fk_name = 'user'

# Esta classe personaliza a tela de administração do Usuário
class CustomUserAdmin(BaseUserAdmin):
    # Adiciona o PerfilInline à tela de edição do usuário
    inlines = (PerfilInline,)
    
    # Adiciona a coluna 'pontos' e otimiza a consulta ao banco de dados
    list_display = ('username', 'email', 'first_name', 'is_staff', 'get_pontos')
    list_select_related = ('perfil',) # OTIMIZAÇÃO: Busca o perfil junto com o usuário, evitando consultas extras.

    ordering = ('username',)

    @admin.display(description='Pontos do Perfil')
    def get_pontos(self, obj):
        # Esta função agora é mais rápida por causa do 'list_select_related'
        if hasattr(obj, 'perfil'):
            return obj.perfil.pontos
        return 0

# Esta classe personaliza a tela de administração dos Posts
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'data_criacao')
    list_filter = ('autor', 'data_criacao', 'tags')
    search_fields = ('titulo', 'conteudo')
    date_hierarchy = 'data_criacao'
    list_select_related = ('autor',) # OTIMIZAÇÃO: Busca o autor em uma única consulta.

# Esta classe personaliza a tela de administração dos Comentários
@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('post', 'autor', 'data', 'texto_curto')
    list_filter = ('autor', 'data')
    search_fields = ('texto',)
    list_select_related = ('post', 'autor',) # OTIMIZAÇÃO: Busca o post e o autor de uma vez.
    
    # MELHORIA: Mostra apenas uma parte do comentário na lista
    @admin.display(description='Texto do Comentário')
    def texto_curto(self, obj):
        return (obj.texto[:75] + '...') if len(obj.texto) > 75 else obj.texto

# Esta classe personaliza a tela de administração das Curtidas
@admin.register(Curtida)
class CurtidaAdmin(admin.ModelAdmin):
    list_display = ('post', 'usuario', 'data')
    list_filter = ('usuario', 'data')
    list_select_related = ('post', 'usuario',) # OTIMIZAÇÃO

# Remove o registro padrão do User e registra novamente com nossa versão personalizada
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

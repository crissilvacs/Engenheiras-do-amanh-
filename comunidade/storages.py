from django.core.files.storage import FileSystemStorage
from django.urls import reverse

class ProtectedMediaStorage(FileSystemStorage):
    def url(self, name):
        # Gera URL para a rota protegida (em vez de /media/…)
        return reverse('protected_media', args=[name])

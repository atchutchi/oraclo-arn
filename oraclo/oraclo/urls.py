"""
URL configuration for oraclo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# oraclo/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

# Função simples para a página inicial
def home(request):
    return HttpResponse("<h1>Bem-vindo ao Oraclo!</h1><p>Use os links acima para navegar.</p>")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('file-manager/', include('file_manager.urls')),  # Inclui as URLs do app file_manager
    path('', home, name='home'),  # Página inicial
]

# Adicionar URLs para servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
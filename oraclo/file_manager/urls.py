# file_manager/urls.py
from django.urls import path
from . import views

app_name = 'file_manager'

urlpatterns = [
    # Home
    path('', views.HomeView.as_view(), name='home'),
    
    # Documentos
    path('documents/upload/', views.DocumentUploadView.as_view(), name='document_upload'),
    path('documents/<int:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('documents/', views.DocumentListView.as_view(), name='document_list'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document_delete'),
    
    # Categorias
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # Regulamentos
    path('regulations/', views.RegulationListView.as_view(), name='regulation_list'),
    path('regulations/<int:pk>/', views.RegulationDetailView.as_view(), name='regulation_detail'),
    
    # APIs
    path('api/chat/', views.DocumentChatAPIView.as_view(), name='document_chat'),
    path('api/search/', views.DocumentSearchAPIView.as_view(), name='document_search'),
]
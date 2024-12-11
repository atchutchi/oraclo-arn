# file_manager/urls.py
from django.urls import path
from . import views

app_name = 'file_manager'

urlpatterns = [
    # Documentos
    path('', views.DocumentListView.as_view(), name='document_list'),  # http://localhost:8000/file-manager/
    path('documents/<int:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),  # http://localhost:8000/file-manager/documents/1/
    path('documents/upload/', views.DocumentUploadView.as_view(), name='document_upload'),  # http://localhost:8000/file-manager/documents/upload/
    
    # Categorias
    path('categories/', views.CategoryListView.as_view(), name='category_list'),  # http://localhost:8000/file-manager/categories/
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),  # http://localhost:8000/file-manager/categories/1/
    
    # Regulamentos
    path('regulations/', views.RegulationListView.as_view(), name='regulation_list'),  # http://localhost:8000/file-manager/regulations/
    path('regulations/<int:pk>/', views.RegulationDetailView.as_view(), name='regulation_detail'),  # http://localhost:8000/file-manager/regulations/1/
    
    # APIs
    path('api/documents/', views.DocumentAPIView.as_view(), name='document_api'),
    path('api/search/', views.DocumentSearchAPIView.as_view(), name='document_search'),
    path('api/chat/', views.DocumentChatAPIView.as_view(), name='document_chat'),
]
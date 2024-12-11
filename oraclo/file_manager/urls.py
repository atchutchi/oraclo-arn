# file_manager/urls.py
from django.urls import path
from . import views

app_name = 'file_manager'

urlpatterns = [
    # Visualização de documentos
    path('', views.DocumentListView.as_view(), name='document_list'),
    path('document/<int:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('document/upload/', views.DocumentUploadView.as_view(), name='document_upload'),
    path('document/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document_delete'),
    
    # API endpoints
    path('api/documents/', views.DocumentAPIView.as_view(), name='document_api'),
    path('api/search/', views.DocumentSearchAPIView.as_view(), name='document_search'),
    path('api/chat/', views.DocumentChatAPIView.as_view(), name='document_chat'),
    
    # Categorias
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('category/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # Regulamentos
    path('regulations/', views.RegulationListView.as_view(), name='regulation_list'),
    path('regulation/<int:pk>/', views.RegulationDetailView.as_view(), name='regulation_detail'),
]
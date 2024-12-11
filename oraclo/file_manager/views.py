# file_manager/views.py
import json
from typing import Any, Dict
from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.views import View
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Document, DocumentCategory, Regulation, DocumentEmbedding
from .services.document_processor import DocumentProcessor
from .utils.file_handlers import FileProcessor, get_file_info
from .forms import DocumentUploadForm, DocumentSearchForm

class DocumentListView(LoginRequiredMixin, ListView):
    """
    Exibe uma lista paginada de documentos com opções de filtro e pesquisa.
    """
    model = Document
    template_name = 'file_manager/document_list.html'
    context_object_name = 'documents'
    paginate_by = 10

    def get_queryset(self):
        queryset = Document.objects.all().order_by('-created_at')
        
        # Aplicar filtros
        doc_type = self.request.GET.get('type')
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)
            
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Aplicar pesquisa
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_types'] = Document.DocumentType.choices
        context['document_statuses'] = Document.DocumentStatus.choices
        context['search_form'] = DocumentSearchForm(self.request.GET or None)
        return context

class DocumentDetailView(LoginRequiredMixin, DetailView):
    """
    Exibe detalhes de um documento específico, incluindo seu conteúdo e metadados.
    """
    model = Document
    template_name = 'file_manager/document_detail.html'
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document = self.get_object()
        
        # Adicionar informações do arquivo
        if document.file_path:
            context['file_info'] = get_file_info(document.file_path)
        
        # Adicionar regulamentos relacionados
        context['regulations'] = document.regulations.all()
        
        # Adicionar histórico de processamento
        context['processing_history'] = document.metadata.get('processing_history', [])
        
        return context

class DocumentUploadView(LoginRequiredMixin, CreateView):
    """
    Permite o upload de novos documentos com processamento automático.
    """
    model = Document
    form_class = DocumentUploadForm
    template_name = 'file_manager/document_upload.html'
    success_url = reverse_lazy('file_manager:document_list')

    def form_valid(self, form):
        try:
            # Salvar o arquivo
            document = form.save(commit=False)
            document.save()

            # Processar o documento
            processor = DocumentProcessor()
            file_processor = FileProcessor()

            # Processar arquivo
            file_result = file_processor.process_file(
                document.file_path,
                category=form.cleaned_data.get('category', 'general')
            )

            # Processar conteúdo e gerar embeddings
            processed_doc = processor.process_document(
                file_result['new_path'],
                title=document.title
            )

            messages.success(self.request, 'Documento enviado e processado com sucesso.')
            return super().form_valid(form)

        except Exception as e:
            messages.error(self.request, f'Erro no processamento: {str(e)}')
            return super().form_invalid(form)

class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    """
    Permite a exclusão de documentos.
    """
    model = Document
    success_url = reverse_lazy('file_manager:document_list')
    template_name = 'file_manager/document_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(request, 'Documento excluído com sucesso.')
            return response
        except Exception as e:
            messages.error(request, f'Erro ao excluir documento: {str(e)}')
            return self.render_to_response(self.get_context_data())

class DocumentAPIView(APIView):
    """
    API para operações CRUD em documentos.
    """
    def get(self, request, format=None):
        """Lista todos os documentos."""
        documents = Document.objects.all()
        data = [{
            'id': doc.id,
            'title': doc.title,
            'type': doc.document_type,
            'status': doc.status,
            'created_at': doc.created_at
        } for doc in documents]
        return Response(data)

    def post(self, request, format=None):
        """Cria um novo documento via API."""
        try:
            processor = DocumentProcessor()
            file_obj = request.FILES.get('file')
            
            if not file_obj:
                return Response(
                    {'error': 'Nenhum arquivo enviado'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            document = processor.process_document(file_obj.temporary_file_path())
            return Response({
                'id': document.id,
                'title': document.title,
                'status': document.status
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DocumentSearchAPIView(APIView):
    """
    API para pesquisa semântica em documentos.
    """
    def post(self, request, format=None):
        try:
            query = request.data.get('query')
            if not query:
                return Response(
                    {'error': 'Query não fornecida'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            processor = DocumentProcessor()
            qa_chain = processor.setup_qa_chain(Document.objects.all())
            
            response = qa_chain.run(query)
            
            return Response({
                'answer': response,
                'sources': [doc.title for doc in response.source_documents]
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DocumentChatAPIView(APIView):
    """
    API para interação conversacional com documentos.
    """
    def post(self, request, format=None):
        try:
            question = request.data.get('question')
            chat_history = request.data.get('history', [])
            
            if not question:
                return Response(
                    {'error': 'Pergunta não fornecida'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            processor = DocumentProcessor()
            qa_chain = processor.setup_qa_chain(Document.objects.all())
            
            response = qa_chain({
                "question": question,
                "chat_history": chat_history
            })
            
            return Response({
                'answer': response['answer'],
                'sources': [doc.title for doc in response.get('source_documents', [])]
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CategoryListView(LoginRequiredMixin, ListView):
    """
    Lista todas as categorias de documentos.
    """
    model = DocumentCategory
    template_name = 'file_manager/category_list.html'
    context_object_name = 'categories'

class CategoryDetailView(LoginRequiredMixin, DetailView):
    """
    Exibe detalhes de uma categoria específica e seus documentos.
    """
    model = DocumentCategory
    template_name = 'file_manager/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = Document.objects.filter(
            categories=self.object
        ).order_by('-created_at')
        return context

class RegulationListView(LoginRequiredMixin, ListView):
    """
    Lista todos os regulamentos.
    """
    model = Regulation
    template_name = 'file_manager/regulation_list.html'
    context_object_name = 'regulations'

class RegulationDetailView(LoginRequiredMixin, DetailView):
    """
    Exibe detalhes de um regulamento específico.
    """
    model = Regulation
    template_name = 'file_manager/regulation_detail.html'
    context_object_name = 'regulation'
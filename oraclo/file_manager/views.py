# file_manager/views.py
import logging
import json
from typing import List, Any, Dict
from django.views.generic import ListView, DetailView, CreateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.views import View
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from django.conf import settings
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import FAISS

# Importações dos modelos
from .models import (
    Document,
    DocumentCategory,
    DocumentEmbedding,
    Regulation,
    TimeStampedModel
)

# Importações de serviços e utilitários
from .services.document_processor import DocumentProcessor
from .utils.file_handlers import FileProcessor, get_file_info
from .forms import DocumentUploadForm, DocumentSearchForm


logger = logging.getLogger(__name__)


class HomeView(LoginRequiredMixin, TemplateView):
    """
    View da página inicial do sistema.
    
    Exibe estatísticas gerais e acesso rápido às principais funcionalidades.
    """
    template_name = 'file_manager/home.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        # Estatísticas básicas
        context['document_count'] = Document.objects.count()
        context['category_count'] = DocumentCategory.objects.count()
        context['regulation_count'] = Regulation.objects.count()
        
        # Documentos recentes (últimos 7 dias)
        last_week = timezone.now() - timezone.timedelta(days=7)
        context['recent_count'] = Document.objects.filter(
            created_at__gte=last_week
        ).count()
        
        # Documentos por tipo
        context['documents_by_type'] = Document.objects.values(
            'document_type'
        ).annotate(
            count=Count('id')
        )
        
        # Regulamentos ativos
        context['active_regulations'] = Regulation.objects.filter(
            status='ACTIVE'
        ).count()
        
        return context


class DocumentListView(LoginRequiredMixin, ListView):
    """
    Lista paginada de documentos com filtros e pesquisa.
    """
    model = Document
    template_name = 'file_manager/document_list.html'
    context_object_name = 'documents'
    paginate_by = 10

    def get_queryset(self):
        queryset = Document.objects.prefetch_related(
            'categories',
            'regulations'
        ).order_by('-created_at')
        
        # Aplicar filtros
        doc_type = self.request.GET.get('type')
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)
            
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(categories__id=category)
            
        # Pesquisa global
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(metadata__icontains=search_query)
            ).distinct()
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'document_types': Document.DocumentType.choices,
            'document_statuses': Document.DocumentStatus.choices,
            'categories': DocumentCategory.objects.all(),
            'search_form': DocumentSearchForm(self.request.GET or None)
        })
        return context

class DocumentDetailView(LoginRequiredMixin, DetailView):
    """
    Exibe detalhes completos de um documento.
    """
    model = Document
    template_name = 'file_manager/document_detail.html'
    context_object_name = 'document'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        document = self.get_object()
        
        # Informações do arquivo
        if document.file_path:
            context['file_info'] = get_file_info(document.file_path)
        
        # Regulamentos relacionados
        context['regulations'] = document.regulations.all().select_related('document')
        
        # Histórico de processamento
        context['processing_history'] = document.metadata.get('processing_history', [])
        
        # Categorias
        context['categories'] = document.categories.all()
        
        # Embeddings
        context['embeddings'] = document.embeddings.all()
        
        return context


class DocumentUploadView(LoginRequiredMixin, CreateView):
    """
    Permite upload e processamento de novos documentos.
    """
    model = Document
    form_class = DocumentUploadForm
    template_name = 'file_manager/document_upload.html'
    success_url = reverse_lazy('file_manager:document_list')

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['categories'] = DocumentCategory.objects.all()
        context['allowed_types'] = [
            x[1] for x in Document.DocumentType.choices
        ]
        return context

    def form_valid(self, form):
        try:
            # Salvar documento inicialmente
            document = form.save(commit=False)
            document.status = Document.DocumentStatus.PROCESSING
            document.save()

            # Processar o arquivo
            processor = DocumentProcessor()
            file_processor = FileProcessor()

            # Processar e organizar arquivo
            file_result = file_processor.process_file(
                document.file_path,
                category=form.cleaned_data.get('category', 'general')
            )

            # Processar conteúdo e gerar embeddings
            processed_doc = processor.process_document(
                file_result['new_path'],
                title=document.title
            )

            # Vincular categorias se fornecidas
            categories = form.cleaned_data.get('categories', [])
            if categories:
                document.categories.set(categories)

            messages.success(
                self.request,
                'Documento enviado e processado com sucesso.'
            )
            return super().form_valid(form)

        except Exception as e:
            messages.error(
                self.request,
                f'Erro no processamento: {str(e)}'
            )
            document.status = Document.DocumentStatus.ERROR
            document.metadata['error'] = str(e)
            document.save()
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

class DocumentChatAPIView(APIView):
    """
    API para interação conversacional inteligente com documentos usando GPT-4.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY
        )
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

    def setup_qa_chain(self, documents: List[Document]) -> ConversationalRetrievalChain:
        """
        Configura a chain de QA com o contexto específico do ORACLO.
        """
        # Criar o prompt do sistema
        system_template = """Você é um assistente especializado do ORACLO, o Sistema de Gestão Documental da 
        Autoridade Reguladora Nacional das TICs da Guiné-Bissau. Use as seguintes regras:

        1. Responda sempre em português de Portugal
        2. Seja profissional mas amigável
        3. Use o contexto dos documentos fornecidos
        4. Se não tiver certeza, diga que precisa de mais informações
        5. Para questões regulatórias, cite as fontes específicas
        6. Mantenha as respostas concisas e relevantes
        7. Use exemplos quando apropriado

        Contexto atual: {context}
        Histórico da conversa: {chat_history}
        """

        # Criar vetores de documentos
        doc_contents = [
            doc.content for doc in documents if doc.content
        ]
        vectorstore = FAISS.from_texts(
            doc_contents,
            self.embeddings
        )

        # Configurar o prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template("{question}")
        ])

        # Criar e retornar a chain
        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=vectorstore.as_retriever(
                search_kwargs={"k": 3}
            ),
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": prompt},
            return_source_documents=True,
            verbose=True
        )

    def post(self, request, format=None):
        """
        Processa perguntas e mantém contexto da conversa.
        """
        try:
            question = request.data.get('question')
            chat_history = request.data.get('history', [])
            
            if not question:
                return Response(
                    {'error': 'Pergunta não fornecida'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Buscar documentos processados
            documents = Document.objects.filter(
                status=Document.DocumentStatus.PROCESSED
            ).select_related()
            
            # Configurar e executar a chain
            qa_chain = self.setup_qa_chain(documents)
            
            # Atualizar histórico do chat
            for exchange in chat_history:
                if isinstance(exchange, dict):
                    self.memory.save_context(
                        {"input": exchange.get('question', '')},
                        {"output": exchange.get('answer', '')}
                    )

            # Processar a pergunta
            result = qa_chain({
                "question": question,
                "chat_history": chat_history
            })
            
            # Extrair fontes
            sources = []
            if hasattr(result, 'source_documents'):
                sources = [
                    {
                        'title': doc.title,
                        'type': doc.document_type,
                        'id': doc.id
                    } for doc in result.source_documents
                ]

            response_data = {
                'answer': result['answer'],
                'sources': sources,
                'confidence': 0.95  # Exemplo - pode ser calculado baseado no score de similaridade
            }

            logger.info(f"Chat processado com sucesso: {question[:50]}...")
            return Response(response_data)

        except Exception as e:
            logger.error(f"Erro no chat: {str(e)}")
            return Response(
                {
                    'error': 'Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente.',
                    'details': str(e) if settings.DEBUG else None
                },
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


class DocumentChatAPIView(APIView):
    """
    API para interação conversacional com documentos usando IA.
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

            # Inicializar processador de documentos
            processor = DocumentProcessor()

            # Buscar documentos relevantes
            documents = Document.objects.filter(status=Document.DocumentStatus.PROCESSED)
            
            # Configurar e executar a chain de QA
            qa_chain = processor.setup_qa_chain(documents)
            
            # Processar a pergunta
            response = qa_chain({
                "question": question,
                "chat_history": chat_history
            })
            
            return Response({
                'answer': response['answer'],
                'sources': [doc.title for doc in response.get('source_documents', [])]
            })

        except Exception as e:
            logger.error(f"Erro no chat: {str(e)}")
            return Response(
                {'error': 'Erro ao processar pergunta'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
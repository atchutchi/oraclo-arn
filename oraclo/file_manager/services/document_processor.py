# file_manager/services/document_processor.py
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from langchain.text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.vectorstores import SQLAlchemyVectorStore

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    EasyOcrOptions,
    TesseractOcrOptions
)

from django.conf import settings
from django.db import transaction

from ..models import Document, DocumentEmbedding, DocumentCategory, Regulation

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Processador de documentos que integra Docling e LangChain para extrair,
    processar e indexar conteúdo de diferentes tipos de documentos.
    """

    def __init__(self):
        """
        Inicializa o processador de documentos com as configurações necessárias.
        """
        self.doc_converter = self._setup_document_converter()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY
        )
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0,
            api_key=settings.OPENAI_API_KEY
        )

    def _setup_document_converter(self) -> DocumentConverter:
        """
        Configura o conversor de documentos do Docling com as opções apropriadas.
        """
        # Configuração para PDF com OCR
        pdf_options = PdfPipelineOptions()
        pdf_options.do_ocr = True
        pdf_options.do_table_structure = True
        pdf_options.generate_page_images = True
        pdf_options.images_scale = 2.0
        
        # Configurar diferentes opções de OCR
        pdf_options.ocr_options = TesseractOcrOptions(
            force_full_page_ocr=True
        )

        return DocumentConverter(
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.DOCX,
                InputFormat.IMAGE,
                InputFormat.HTML,
                InputFormat.TXT
            ]
        )

    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calcula o hash SHA-256 de um arquivo.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _detect_document_type(self, file_path: str) -> Document.DocumentType:
        """
        Detecta o tipo do documento baseado na extensão do arquivo.
        """
        ext = Path(file_path).suffix.lower()
        type_mapping = {
            '.pdf': Document.DocumentType.PDF,
            '.docx': Document.DocumentType.DOCX,
            '.txt': Document.DocumentType.TXT,
            '.jpg': Document.DocumentType.IMAGE,
            '.jpeg': Document.DocumentType.IMAGE,
            '.png': Document.DocumentType.IMAGE,
            '.html': Document.DocumentType.HTML,
        }
        return type_mapping.get(ext, Document.DocumentType.OTHER)

    def _extract_metadata(self, doc_content: Any) -> Dict[str, Any]:
        """
        Extrai metadados do documento processado.
        """
        metadata = {
            'num_pages': getattr(doc_content, 'num_pages', 1),
            'has_images': False,
            'has_tables': False,
            'language': 'pt'  # Implementar detecção de idioma se necessário
        }

        # Adicionar lógica específica para diferentes tipos de documentos
        if hasattr(doc_content, 'images'):
            metadata['has_images'] = True
            metadata['num_images'] = len(doc_content.images)

        if hasattr(doc_content, 'tables'):
            metadata['has_tables'] = True
            metadata['num_tables'] = len(doc_content.tables)

        return metadata

    @transaction.atomic
    def process_document(self, file_path: str, title: Optional[str] = None) -> Document:
        """
        Processa um documento, extraindo seu conteúdo e criando embeddings.
        
        Args:
            file_path: Caminho do arquivo a ser processado
            title: Título opcional do documento
            
        Returns:
            Document: Instância do modelo Document processado
        """
        try:
            # Verificar existência do arquivo
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

            # Calcular hash e verificar duplicidade
            file_hash = self._calculate_file_hash(file_path)
            if Document.objects.filter(file_hash=file_hash).exists():
                raise ValueError(f"Documento já processado anteriormente: {file_path}")

            # Criar registro inicial do documento
            document = Document.objects.create(
                title=title or Path(file_path).name,
                file_path=file_path,
                document_type=self._detect_document_type(file_path),
                status=Document.DocumentStatus.PROCESSING,
                file_hash=file_hash
            )

            # Processar o documento com Docling
            conversion_result = self.doc_converter.convert(file_path)
            
            # Extrair conteúdo e metadados
            content = conversion_result.document.export_to_markdown()
            metadata = self._extract_metadata(conversion_result.document)
            
            # Dividir o conteúdo em chunks para processamento
            text_chunks = self.text_splitter.split_text(content)
            
            # Gerar embeddings
            for chunk in text_chunks:
                embedding_vector = self.embeddings.embed_query(chunk)
                DocumentEmbedding.objects.create(
                    document=document,
                    vector=embedding_vector,
                    model_name="text-embedding-ada-002"
                )

            # Atualizar documento com conteúdo processado
            document.content = content
            document.metadata = metadata
            document.status = Document.DocumentStatus.PROCESSED
            document.save()

            return document

        except Exception as e:
            logger.error(f"Erro ao processar documento {file_path}: {str(e)}")
            if 'document' in locals():
                document.status = Document.DocumentStatus.ERROR
                document.metadata = {'error': str(e)}
                document.save()
            raise

    def process_batch(self, file_paths: List[str]) -> List[Document]:
        """
        Processa um lote de documentos.
        """
        processed_documents = []
        for file_path in file_paths:
            try:
                doc = self.process_document(file_path)
                processed_documents.append(doc)
            except Exception as e:
                logger.error(f"Erro ao processar {file_path}: {e}")
        return processed_documents

    def setup_qa_chain(self, documents: List[Document]) -> ConversationalRetrievalChain:
        """
        Configura uma chain de pergunta e resposta para os documentos processados.
        """
        # Criar vetor store com os embeddings dos documentos
        vectorstore = SQLAlchemyVectorStore(
            self.embeddings,
            connection_string=settings.DATABASE_URL,
            documents_table="file_manager_documentembedding",
            embeddings_table="file_manager_documentembedding_vectors"
        )
        
        # Configurar chain de QA
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=vectorstore.as_retriever(),
            return_source_documents=True
        )
        
        return qa_chain

    def classify_regulation(self, document: Document) -> Optional[Regulation]:
        """
        Classifica um documento como regulamentação se apropriado.
        """
        # Implementar lógica de classificação usando LLM
        prompt = f"""
        Analise o seguinte documento e determine se é um documento regulatório do setor de telecomunicações.
        Se for, extraia as informações relevantes.
        
        Documento: {document.content[:1000]}...
        """
        
        response = self.llm.predict(prompt)
        
        # Processar a resposta e criar Regulation se apropriado
        # (Implementar lógica específica baseada nas necessidades)
        
        return None  # Ou retornar instância de Regulation
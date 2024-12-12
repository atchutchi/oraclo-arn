# file_manager/services/document_processor.py

import hashlib
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Importações do LangChain atualizadas
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

# Importações do Docling
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
    def __init__(self):
        self.doc_converter = self._setup_document_converter()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            add_start_index=True
        )
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            model="text-embedding-ada-002"
        )
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

    def _setup_document_converter(self) -> DocumentConverter:
        pdf_options = PdfPipelineOptions(
            do_ocr=True,
            do_table_structure=True,
            generate_page_images=True,
            images_scale=2.0,
            ocr_options=TesseractOcrOptions(
                force_full_page_ocr=True,
                language='por'
            )
        )

        return DocumentConverter(
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.DOCX,
                InputFormat.IMAGE,
                InputFormat.HTML,
                'txt'
            ],
            pdf_options=pdf_options
        )

    def _calculate_file_hash(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _detect_document_type(self, file_path: str) -> Document.DocumentType:
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
        metadata = {
            'num_pages': getattr(doc_content, 'num_pages', 1),
            'has_images': False,
            'has_tables': False,
            'language': 'pt'
        }

        if hasattr(doc_content, 'images'):
            metadata['has_images'] = True
            metadata['num_images'] = len(doc_content.images)

        if hasattr(doc_content, 'tables'):
            metadata['has_tables'] = True
            metadata['num_tables'] = len(doc_content.tables)

        return metadata

    @transaction.atomic
    def process_document(self, file_path: str, title: Optional[str] = None) -> Document:
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

            file_hash = self._calculate_file_hash(file_path)
            if Document.objects.filter(file_hash=file_hash).exists():
                raise ValueError(f"Documento já processado anteriormente: {file_path}")

            document = Document.objects.create(
                title=title or Path(file_path).name,
                file_path=file_path,
                document_type=self._detect_document_type(file_path),
                status=Document.DocumentStatus.PROCESSING,
                file_hash=file_hash
            )

            conversion_result = self.doc_converter.convert(file_path)
            content = conversion_result.document.export_to_markdown()
            metadata = self._extract_metadata(conversion_result.document)
            
            text_chunks = self.text_splitter.split_text(content)
            
            for chunk in text_chunks:
                embedding_vector = self.embeddings.embed_query(chunk)
                DocumentEmbedding.objects.create(
                    document=document,
                    vector=embedding_vector,
                    model_name="text-embedding-ada-002"
                )

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
        processed_documents = []
        for file_path in file_paths:
            try:
                doc = self.process_document(file_path)
                processed_documents.append(doc)
            except Exception as e:
                logger.error(f"Erro ao processar {file_path}: {e}")
        return processed_documents

    def setup_qa_chain(self, documents: List[Document]) -> ConversationalRetrievalChain:
        documents_texts = []
        for doc in documents:
            if doc.content:
                chunks = self.text_splitter.split_text(doc.content)
                documents_texts.extend(chunks)

        vectorstore = FAISS.from_texts(
            documents_texts,
            self.embeddings,
            metadatas=[{"source": f"doc_{i}"} for i in range(len(documents_texts))]
        )

        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": 5,
                    "fetch_k": 10
                }
            ),
            memory=self.memory,
            return_source_documents=True,
            verbose=True
        )

        return qa_chain

    def classify_regulation(self, document: Document) -> Optional[Regulation]:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Você é um especialista em análise de regulamentos do setor de telecomunicações.
                Analise o documento e extraia:
                1. Tipo de regulamento
                2. Escopo de aplicação
                3. Data de vigência
                4. Principais disposições
                5. Relação com outros regulamentos
                
                Retorne a análise em formato JSON."""),
                ("human", f"Documento: {document.content[:2000]}...")
            ])

            response = self.llm.invoke(prompt)
            
            try:
                analysis = json.loads(response.content)
                if analysis.get('is_regulation'):
                    return Regulation.objects.create(
                        title=analysis.get('title'),
                        regulation_type=analysis.get('type'),
                        document=document,
                        effective_date=analysis.get('effective_date'),
                        status='ACTIVE'
                    )
            except json.JSONDecodeError:
                logger.error(f"Erro ao processar resposta da IA para documento {document.id}")
                
            return None

        except Exception as e:
            logger.error(f"Erro ao classificar regulamento: {str(e)}")
            return None
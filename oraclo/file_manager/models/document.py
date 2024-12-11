# file_manager/models/document.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import TimeStampedModel

class Document(TimeStampedModel):
    """
    Modelo principal para documentos processados.
    """
    class DocumentType(models.TextChoices):
        PDF = 'PDF', _('PDF Document')
        DOCX = 'DOCX', _('Word Document')
        TXT = 'TXT', _('Text File')
        IMAGE = 'IMAGE', _('Image')
        HTML = 'HTML', _('HTML Document')
        OTHER = 'OTHER', _('Other')

    class DocumentStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pendente')
        PROCESSING = 'PROCESSING', _('Processando')
        PROCESSED = 'PROCESSED', _('Processado')
        ERROR = 'ERROR', _('Erro')
        
    title = models.CharField(
        _('Título'),
        max_length=255,
        help_text=_('Título do documento')
    )
    
    file_path = models.CharField(
        _('Caminho do Arquivo'),
        max_length=512,
        help_text=_('Caminho do arquivo no sistema')
    )
    
    content = models.TextField(
        _('Conteúdo'),
        blank=True,
        help_text=_('Conteúdo extraído do documento')
    )
    
    document_type = models.CharField(
        _('Tipo de Documento'),
        max_length=10,
        choices=DocumentType.choices,
        default=DocumentType.OTHER
    )
    
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.PENDING
    )
    
    file_hash = models.CharField(
        _('Hash do Arquivo'),
        max_length=64,
        blank=True,
        help_text=_('Hash SHA-256 do arquivo para verificação de duplicidade')
    )
    
    metadata = models.JSONField(
        _('Metadados'),
        default=dict,
        help_text=_('Metadados adicionais do documento')
    )

    def __str__(self):
        return f"{self.title} ({self.document_type})"
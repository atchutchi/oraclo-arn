# file_manager/models/regulation.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import TimeStampedModel
from .document import Document

class Regulation(TimeStampedModel):
    """
    Modelo para documentos regulatórios específicos do setor de telecomunicações.
    """
    title = models.CharField(
        _('Título'),
        max_length=255
    )
    
    regulation_type = models.CharField(
        _('Tipo de Regulamento'),
        max_length=100,
        choices=[
            ('LAW', _('Lei')),
            ('DECREE', _('Decreto')),
            ('RESOLUTION', _('Resolução')),
            ('NORMATIVE', _('Normativa')),
            ('POLICY', _('Política')),
        ]
    )
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='regulations'
    )
    
    effective_date = models.DateField(
        _('Data de Vigência'),
        null=True,
        blank=True
    )
    
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=[
            ('ACTIVE', _('Ativo')),
            ('INACTIVE', _('Inativo')),
            ('PENDING', _('Pendente')),
            ('REVOKED', _('Revogado')),
        ],
        default='ACTIVE'
    )

    class Meta:
        verbose_name = _('Regulamento')
        verbose_name_plural = _('Regulamentos')
        ordering = ['-effective_date']

    def __str__(self):
        return self.title
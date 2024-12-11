# file_manager/models/category.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import TimeStampedModel

class DocumentCategory(TimeStampedModel):
    """
    Modelo para categorização de documentos.
    """
    name = models.CharField(
        _('Nome'),
        max_length=100,
        unique=True
    )
    
    description = models.TextField(
        _('Descrição'),
        blank=True
    )
    
    parent = models.ForeignKey(
        'self',
        verbose_name=_('Categoria Pai'),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    class Meta:
        verbose_name = _('Categoria')
        verbose_name_plural = _('Categorias')
        ordering = ['name']

    def __str__(self):
        return self.name
# file_manager/models/base.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class TimeStampedModel(models.Model):
    """
    Um modelo base abstrato que fornece campos de auto-atualização
    created_at e updated_at.
    """
    created_at = models.DateTimeField(
        _('Data de Criação'),
        auto_now_add=True,
        help_text=_('Data e hora de criação do registro')
    )
    updated_at = models.DateTimeField(
        _('Última Atualização'),
        auto_now=True,
        help_text=_('Data e hora da última atualização')
    )

    class Meta:
        abstract = True
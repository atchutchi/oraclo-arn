# file_manager/models/embeddings.py
class DocumentEmbedding(TimeStampedModel):
    """
    Modelo para armazenar embeddings de documentos.
    """
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='embeddings'
    )
    
    vector = models.JSONField(
        _('Vetor de Embedding'),
        help_text=_('Vetor de embedding do documento')
    )
    
    model_name = models.CharField(
        _('Modelo de Embedding'),
        max_length=100,
        help_text=_('Nome do modelo usado para gerar o embedding')
    )

    class Meta:
        verbose_name = _('Embedding')
        verbose_name_plural = _('Embeddings')
        indexes = [
            models.Index(fields=['document', 'model_name'])
        ]
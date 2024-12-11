# file_manager/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Document, DocumentCategory, DocumentEmbedding, Regulation

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'status', 'created_at', 'file_link')
    list_filter = ('document_type', 'status', 'created_at')
    search_fields = ('title', 'content')
    readonly_fields = ('file_hash', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'

    def file_link(self, obj):
        if obj.file_path:
            return format_html('<a href="{}" target="_blank">Abrir arquivo</a>', obj.file_path)
        return "Sem arquivo"
    file_link.short_description = "Arquivo"

@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')

@admin.register(DocumentEmbedding)
class DocumentEmbeddingAdmin(admin.ModelAdmin):
    list_display = ('document', 'model_name', 'created_at')
    list_filter = ('model_name', 'created_at')
    search_fields = ('document__title',)

@admin.register(Regulation)
class RegulationAdmin(admin.ModelAdmin):
    list_display = ('title', 'regulation_type', 'status', 'effective_date')
    list_filter = ('regulation_type', 'status', 'effective_date')
    search_fields = ('title', 'document__content')
    date_hierarchy = 'effective_date'
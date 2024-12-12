# file_manager/forms.py
from django import forms
from .models import Document, DocumentCategory, Regulation

class DocumentUploadForm(forms.ModelForm):
    """
    Formulário para upload de documentos.
    """
    class Meta:
        model = Document
        fields = ['title', 'file_path', 'document_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file_path': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.txt'}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
        }

class DocumentSearchForm(forms.Form):
    """
    Formulário para pesquisa de documentos.
    """
    q = forms.CharField(
        label='Pesquisar',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pesquisar documentos...'
        })
    )
    type = forms.ChoiceField(
        label='Tipo',
        required=False,
        choices=[('', 'Todos os tipos')] + list(Document.DocumentType.choices),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        label='Status',
        required=False,
        choices=[('', 'Todos os status')] + list(Document.DocumentStatus.choices),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class CategoryForm(forms.ModelForm):
    """
    Formulário para criação/edição de categorias.
    """
    class Meta:
        model = DocumentCategory
        fields = ['name', 'description', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
        }

class RegulationForm(forms.ModelForm):
    """
    Formulário para criação/edição de regulamentos.
    """
    class Meta:
        model = Regulation
        fields = ['title', 'regulation_type', 'document', 'effective_date', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'regulation_type': forms.Select(attrs={'class': 'form-control'}),
            'document': forms.Select(attrs={'class': 'form-control'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
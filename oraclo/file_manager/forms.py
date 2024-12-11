# file_manager/forms.py
from django import forms
from .models import Document, DocumentCategory

class DocumentUploadForm(forms.ModelForm):
    """
    Formulário para upload de documentos.
    """
    category = forms.ModelChoiceField(
        queryset=DocumentCategory.objects.all(),
        required=False,
        empty_label="Selecione uma categoria"
    )

    class Meta:
        model = Document
        fields = ['title', 'file_path', 'document_type']
        
    def clean_file_path(self):
        file = self.cleaned_data.get('file_path')
        if file:
            if file.size > 10 * 1024 * 1024:  # 10MB limit
                raise forms.ValidationError('O arquivo não pode ser maior que 10MB')
        return file

class DocumentSearchForm(forms.Form):
    """
    Formulário para pesquisa de documentos.
    """
    q = forms.CharField(
        required=False,
        label='Pesquisar',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pesquisar documentos...'
        })
    )
    
    document_type = forms.ChoiceField(
        choices=[('', 'Todos os tipos')] + list(Document.DocumentType.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
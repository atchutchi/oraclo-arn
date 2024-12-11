# file_manager/tests/test_views.py
from django.test import TestCase, Client
from django.urls import reverse
from file_manager.models import Document, DocumentCategory, Regulation
from django.contrib.auth.models import User

class FileManagerTestCase(TestCase):
    def setUp(self):
        # Criar usuário para testes
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        # Criar objetos de teste
        self.category = DocumentCategory.objects.create(
            name='Test Category',
            description='Test Description'
        )
        
        self.document = Document.objects.create(
            title='Test Document',
            file_path='/test/path.pdf',
            document_type=Document.DocumentType.PDF,
            status=Document.DocumentStatus.PROCESSED
        )
        
        self.regulation = Regulation.objects.create(
            title='Test Regulation',
            regulation_type='LAW',
            document=self.document
        )

    def test_document_list_view(self):
        response = self.client.get(reverse('file_manager:document_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'file_manager/document_list.html')
        self.assertContains(response, 'Test Document')

    def test_category_list_view(self):
        response = self.client.get(reverse('file_manager:category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'file_manager/category_list.html')
        self.assertContains(response, 'Test Category')

    def test_regulation_list_view(self):
        response = self.client.get(reverse('file_manager:regulation_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'file_manager/regulation_list.html')
        self.assertContains(response, 'Test Regulation')

# file_manager/tests/test_models.py
from django.test import TestCase
from file_manager.models import Document, DocumentCategory, Regulation

class ModelTestCase(TestCase):
    def test_document_creation(self):
        document = Document.objects.create(
            title='Test Document',
            file_path='/test/path.pdf',
            document_type=Document.DocumentType.PDF
        )
        self.assertEqual(str(document), 'Test Document (PDF)')

    def test_category_creation(self):
        category = DocumentCategory.objects.create(
            name='Test Category',
            description='Test Description'
        )
        self.assertEqual(str(category), 'Test Category')

    def test_regulation_creation(self):
        document = Document.objects.create(
            title='Test Document',
            file_path='/test/path.pdf',
            document_type=Document.DocumentType.PDF
        )
        regulation = Regulation.objects.create(
            title='Test Regulation',
            regulation_type='LAW',
            document=document
        )
        self.assertEqual(str(regulation), 'Test Regulation')
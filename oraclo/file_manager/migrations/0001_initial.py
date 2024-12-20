# Generated by Django 5.1.4 on 2024-12-12 10:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Data e hora de criação do registro', verbose_name='Data de Criação')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Data e hora da última atualização', verbose_name='Última Atualização')),
                ('title', models.CharField(help_text='Título do documento', max_length=255, verbose_name='Título')),
                ('file_path', models.CharField(help_text='Caminho do arquivo no sistema', max_length=512, verbose_name='Caminho do Arquivo')),
                ('content', models.TextField(blank=True, help_text='Conteúdo extraído do documento', verbose_name='Conteúdo')),
                ('document_type', models.CharField(choices=[('PDF', 'PDF Document'), ('DOCX', 'Word Document'), ('TXT', 'Text File'), ('IMAGE', 'Image'), ('HTML', 'HTML Document'), ('OTHER', 'Other')], default='OTHER', max_length=10, verbose_name='Tipo de Documento')),
                ('status', models.CharField(choices=[('PENDING', 'Pendente'), ('PROCESSING', 'Processando'), ('PROCESSED', 'Processado'), ('ERROR', 'Erro')], default='PENDING', max_length=20, verbose_name='Status')),
                ('file_hash', models.CharField(blank=True, help_text='Hash SHA-256 do arquivo para verificação de duplicidade', max_length=64, verbose_name='Hash do Arquivo')),
                ('metadata', models.JSONField(default=dict, help_text='Metadados adicionais do documento', verbose_name='Metadados')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DocumentCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Data e hora de criação do registro', verbose_name='Data de Criação')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Data e hora da última atualização', verbose_name='Última Atualização')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Nome')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='file_manager.documentcategory', verbose_name='Categoria Pai')),
            ],
            options={
                'verbose_name': 'Categoria',
                'verbose_name_plural': 'Categorias',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Regulation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Data e hora de criação do registro', verbose_name='Data de Criação')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Data e hora da última atualização', verbose_name='Última Atualização')),
                ('title', models.CharField(max_length=255, verbose_name='Título')),
                ('regulation_type', models.CharField(choices=[('LAW', 'Lei'), ('DECREE', 'Decreto'), ('RESOLUTION', 'Resolução'), ('NORMATIVE', 'Normativa'), ('POLICY', 'Política')], max_length=100, verbose_name='Tipo de Regulamento')),
                ('effective_date', models.DateField(blank=True, null=True, verbose_name='Data de Vigência')),
                ('status', models.CharField(choices=[('ACTIVE', 'Ativo'), ('INACTIVE', 'Inativo'), ('PENDING', 'Pendente'), ('REVOKED', 'Revogado')], default='ACTIVE', max_length=20, verbose_name='Status')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='regulations', to='file_manager.document')),
            ],
            options={
                'verbose_name': 'Regulamento',
                'verbose_name_plural': 'Regulamentos',
                'ordering': ['-effective_date'],
            },
        ),
        migrations.CreateModel(
            name='DocumentEmbedding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Data e hora de criação do registro', verbose_name='Data de Criação')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Data e hora da última atualização', verbose_name='Última Atualização')),
                ('vector', models.JSONField(help_text='Vetor de embedding do documento', verbose_name='Vetor de Embedding')),
                ('model_name', models.CharField(help_text='Nome do modelo usado para gerar o embedding', max_length=100, verbose_name='Modelo de Embedding')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='embeddings', to='file_manager.document')),
            ],
            options={
                'verbose_name': 'Embedding',
                'verbose_name_plural': 'Embeddings',
                'indexes': [models.Index(fields=['document', 'model_name'], name='file_manage_documen_e8c61f_idx')],
            },
        ),
    ]

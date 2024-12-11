# file_manager/utils/file_handlers.py
import os
import shutil
import mimetypes
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict, Optional, Tuple, Union
import magic  # python-magic para detecção de tipo de arquivo
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.text import slugify

logger = logging.getLogger(__name__)

class FileValidator:
    """
    Classe responsável por validar arquivos baseado em diversos critérios.
    """
    
    # Tipos MIME permitidos e suas extensões correspondentes
    ALLOWED_MIMETYPES = {
        'application/pdf': ['.pdf'],
        'application/msword': ['.doc'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
        'text/plain': ['.txt'],
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'application/vnd.ms-excel': ['.xls'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
        'text/html': ['.html', '.htm'],
    }

    # Tamanho máximo de arquivo (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024  

    @classmethod
    def validate_file(cls, file_path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
        """
        Valida um arquivo verificando tipo, tamanho e outros critérios.

        Args:
            file_path: Caminho do arquivo a ser validado

        Returns:
            Tuple[bool, Optional[str]]: (é_válido, mensagem_de_erro)
        """
        file_path = Path(file_path)
        
        try:
            # Verificar existência
            if not file_path.exists():
                return False, "Arquivo não encontrado"

            # Verificar tamanho
            file_size = file_path.stat().st_size
            if file_size > cls.MAX_FILE_SIZE:
                return False, f"Arquivo muito grande. Máximo permitido: {cls.MAX_FILE_SIZE/1024/1024}MB"

            # Verificar tipo MIME
            mime_type = magic.Magic(mime=True).from_file(str(file_path))
            if mime_type not in cls.ALLOWED_MIMETYPES:
                return False, f"Tipo de arquivo não permitido: {mime_type}"

            # Verificar extensão
            if file_path.suffix.lower() not in cls.ALLOWED_MIMETYPES[mime_type]:
                return False, "Extensão de arquivo inválida para o tipo de conteúdo"

            # Verificar se arquivo não está corrompido
            try:
                with open(file_path, 'rb') as f:
                    f.read(1024)  # Tentar ler o início do arquivo
            except Exception as e:
                return False, f"Arquivo corrompido ou ilegível: {str(e)}"

            return True, None

        except Exception as e:
            logger.error(f"Erro ao validar arquivo {file_path}: {str(e)}")
            return False, f"Erro na validação: {str(e)}"

class FileOrganizer:
    """
    Classe responsável por organizar arquivos em uma estrutura padronizada.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Inicializa o organizador de arquivos.

        Args:
            base_dir: Diretório base para armazenamento (opcional)
        """
        self.base_dir = base_dir or Path(settings.MEDIA_ROOT) / 'documents'
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def generate_file_path(self, original_name: str, category: str = 'general') -> Path:
        """
        Gera um caminho de arquivo único e organizado.

        Args:
            original_name: Nome original do arquivo
            category: Categoria do documento

        Returns:
            Path: Caminho completo para o novo arquivo
        """
        # Criar estrutura de diretórios por data
        today = datetime.now()
        year_dir = self.base_dir / str(today.year)
        month_dir = year_dir / f"{today.month:02d}"
        category_dir = month_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # Gerar nome único
        base_name = Path(original_name).stem
        extension = Path(original_name).suffix
        slug_name = slugify(base_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = f"{slug_name}_{timestamp}{extension}"

        return category_dir / new_name

    def organize_file(self, source_path: Union[str, Path], category: str = 'general') -> Path:
        """
        Organiza um arquivo movendo-o para a estrutura adequada.

        Args:
            source_path: Caminho do arquivo fonte
            category: Categoria do documento

        Returns:
            Path: Novo caminho do arquivo
        """
        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {source_path}")

        # Gerar novo caminho
        new_path = self.generate_file_path(source_path.name, category)
        
        # Copiar arquivo
        shutil.copy2(source_path, new_path)
        
        return new_path

class TelecomDocumentHandler:
    """
    Manipulador especializado para documentos do setor de telecomunicações.
    """

    # Categorias específicas para documentos de telecomunicações
    TELECOM_CATEGORIES = {
        'regulatory': ['lei', 'decreto', 'resolução', 'normativa'],
        'technical': ['especificação', 'padrão', 'protocolo'],
        'licensing': ['licença', 'autorização', 'outorga'],
        'spectrum': ['frequência', 'espectro', 'radiodifusão'],
        'infrastructure': ['infraestrutura', 'rede', 'equipamento']
    }

    @staticmethod
    def classify_document(content: str) -> List[str]:
        """
        Classifica um documento nas categorias de telecomunicações.

        Args:
            content: Conteúdo do documento

        Returns:
            List[str]: Lista de categorias identificadas
        """
        categories = []
        content_lower = content.lower()
        
        for category, keywords in TelecomDocumentHandler.TELECOM_CATEGORIES.items():
            if any(keyword in content_lower for keyword in keywords):
                categories.append(category)
        
        return categories

    @staticmethod
    def extract_regulation_info(content: str) -> Dict[str, str]:
        """
        Extrai informações regulatórias do documento.

        Args:
            content: Conteúdo do documento

        Returns:
            Dict[str, str]: Informações regulatórias extraídas
        """
        # Implementar extração de informações específicas
        # Exemplo básico - expandir conforme necessidade
        info = {
            'number': None,
            'date': None,
            'type': None,
            'subject': None
        }
        
        # Adicionar lógica de extração mais sofisticada aqui
        
        return info

class FileProcessor:
    """
    Processador principal que integra todas as funcionalidades de manipulação de arquivos.
    """

    def __init__(self):
        self.validator = FileValidator()
        self.organizer = FileOrganizer()
        self.telecom_handler = TelecomDocumentHandler()

    def process_file(self, file_path: Union[str, Path], category: str = 'general') -> Dict[str, any]:
        """
        Processa um arquivo completamente, realizando todas as etapas necessárias.

        Args:
            file_path: Caminho do arquivo a ser processado
            category: Categoria do documento

        Returns:
            Dict[str, any]: Resultado do processamento
        """
        try:
            # Validar arquivo
            is_valid, error_message = FileValidator.validate_file(file_path)
            if not is_valid:
                raise ValueError(f"Arquivo inválido: {error_message}")

            # Organizar arquivo
            new_path = self.organizer.organize_file(file_path, category)

            # Processar metadados
            result = {
                'original_path': str(file_path),
                'new_path': str(new_path),
                'category': category,
                'processed_at': datetime.now().isoformat(),
                'mime_type': magic.Magic(mime=True).from_file(str(new_path)),
                'size': new_path.stat().st_size
            }

            return result

        except Exception as e:
            logger.error(f"Erro ao processar arquivo {file_path}: {str(e)}")
            raise

def get_file_info(file_path: Union[str, Path]) -> Dict[str, any]:
    """
    Obtém informações detalhadas sobre um arquivo.

    Args:
        file_path: Caminho do arquivo

    Returns:
        Dict[str, any]: Informações do arquivo
    """
    file_path = Path(file_path)
    
    return {
        'name': file_path.name,
        'extension': file_path.suffix,
        'size': file_path.stat().st_size,
        'created': datetime.fromtimestamp(file_path.stat().st_ctime),
        'modified': datetime.fromtimestamp(file_path.stat().st_mtime),
        'mime_type': magic.Magic(mime=True).from_file(str(file_path)),
        'path': str(file_path.absolute())
    }
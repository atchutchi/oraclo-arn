// static/js/document_upload.js

class DocumentUpload {
    constructor() {
        this.fileInput = document.querySelector('input[type="file"]');
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        if (this.fileInput) {
            this.fileInput.addEventListener('change', () => this.handleFileSelect());
        }
    }

    handleFileSelect() {
        const fileName = this.fileInput.files[0]?.name;
        if (fileName) {
            const label = document.querySelector('.form-label');
            label.textContent = `Arquivo selecionado: ${fileName}`;
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new DocumentUpload();
});
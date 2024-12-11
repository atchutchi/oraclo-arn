// static/js/document_detail.js

class DocumentChat {
    constructor() {
        this.chatForm = document.getElementById('chatForm');
        this.chatInput = document.getElementById('chatInput');
        this.chatMessages = document.getElementById('chatMessages');
        this.chatHistory = [];
        this.documentId = document.getElementById('documentId').value;
        this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        this.chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleChatSubmit();
        });
    }

    async handleChatSubmit() {
        const question = this.chatInput.value.trim();
        if (!question) return;

        this.addMessage('user', question);
        this.chatInput.value = '';

        try {
            const response = await this.sendChatRequest(question);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            this.addMessage('assistant', data.answer);
            this.chatHistory.push([question, data.answer]);

        } catch (error) {
            this.addMessage('system', 'Erro ao processar sua pergunta: ' + error.message);
        }
    }

    async sendChatRequest(question) {
        return fetch('/file-manager/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify({
                question: question,
                document_id: this.documentId,
                history: this.chatHistory
            })
        });
    }

    addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;
        messageDiv.innerHTML = content;
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Inicializar quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new DocumentChat();
});
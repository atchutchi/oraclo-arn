// file_manager/static/file_manager/js/chat.js
document.addEventListener('DOMContentLoaded', function () {
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatContainer = document.getElementById('chatContainer');
    let chatHistory = [];

    chatForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const question = chatInput.value.trim();
        if (!question) return;

        // Adicionar mensagem do usuário
        appendMessage(question, 'user');
        chatInput.value = '';

        // Adicionar indicador de digitação
        const typingIndicator = appendTypingIndicator();

        try {
            // Fazer a requisição para a API
            const response = await fetch('/file-manager/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') // Garantir que o CSRF Token seja enviado
                },
                body: JSON.stringify({
                    question: question,
                    history: chatHistory
                })
            });

            if (!response.ok) {
                throw new Error(`Erro na comunicação com o servidor: ${response.statusText}`);
            }

            const data = await response.json();

            // Remover indicador de digitação
            typingIndicator.remove();

            // Verificar se a resposta contém os campos esperados
            if (!data.answer) {
                throw new Error('Resposta inválida recebida do servidor.');
            }

            // Adicionar resposta da IA
            appendMessage(data.answer, 'assistant', data.sources || []);

            // Atualizar histórico
            chatHistory.push({
                question: question,
                answer: data.answer
            });

        } catch (error) {
            console.error('Erro:', error);

            // Remover indicador de digitação em caso de erro
            typingIndicator.remove();

            // Exibir mensagem de erro para o usuário
            appendMessage(
                'Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente.',
                'assistant'
            );
        }
    });

    /**
     * Adiciona uma mensagem ao chat.
     * @param {string} content - O conteúdo da mensagem.
     * @param {string} type - O tipo de mensagem ('user' ou 'assistant').
     * @param {Array} [sources] - Fontes opcionais para exibição.
     */
    function appendMessage(content, type, sources = []) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;

        let html = `
            <div class="message-content">
                <p>${content}</p>
            `;

        // Adicionar fontes, se fornecidas
        if (sources.length > 0) {
            html += `
                <div class="message-sources">
                    <small>Fontes:</small><br>
                    ${sources
                        .map(
                            (source) => `
                        <span class="source-link">
                            <i class="fas fa-file-alt"></i> ${source.title || 'Fonte desconhecida'}
                        </span>
                    `
                        )
                        .join('')}
                </div>
            `;
        }

        html += '</div>';
        messageDiv.innerHTML = html;

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    /**
     * Adiciona um indicador de digitação ao chat.
     * @returns {HTMLElement} O elemento do indicador de digitação.
     */
    function appendTypingIndicator() {
        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'chat-message assistant typing-indicator';
        indicatorDiv.innerHTML = `
            <div class="message-content">
                <p><i class="fas fa-circle"></i><i class="fas fa-circle"></i><i class="fas fa-circle"></i></p>
            </div>
        `;
        chatContainer.appendChild(indicatorDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return indicatorDiv;
    }

    /**
     * Obtém o valor do cookie pelo nome.
     * @param {string} name - O nome do cookie.
     * @returns {string|null} O valor do cookie ou null se não encontrado.
     */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + '=') {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});

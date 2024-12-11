// static/file_manager/js/regulation_detail.js

class RegulationDetailManager {
    constructor() {
        this.regulationId = document.getElementById('regulationId')?.value;
        this.editBtn = document.getElementById('editRegulationBtn');
        this.revokeModal = document.getElementById('revokeModal');
        this.revokeForm = document.getElementById('revokeForm');
        this.confirmRevokeBtn = document.getElementById('confirmRevokeBtn');

        this.initializeEventListeners();
    }

    initializeEventListeners() {
        this.editBtn?.addEventListener('click', () => this.handleEdit());
        this.confirmRevokeBtn?.addEventListener('click', () => this.handleRevoke());

        // Histórico expansível
        document.querySelectorAll('.timeline-item').forEach(item => {
            item.addEventListener('click', () => {
                item.querySelector('.timeline-content').classList.toggle('expanded');
            });
        });
    }

    async handleEdit() {
        try {
            const response = await ApiClient.request(`/file-manager/api/regulations/${this.regulationId}/`);
            // Redirecionar para página de edição com dados pré-preenchidos
            window.location.href = `/file-manager/regulations/${this.regulationId}/edit/`;
        } catch (error) {
            AlertManager.show('Erro ao carregar dados para edição', 'danger');
        }
    }

    async handleRevoke() {
        try {
            const formData = new FormData(this.revokeForm);
            await ApiClient.request(`/file-manager/api/regulations/${this.regulationId}/revoke/`, {
                method: 'POST',
                body: JSON.stringify({
                    reason: formData.get('revoke_reason')
                })
            });

            AlertManager.show('Regulamento revogado com sucesso!', 'success');
            window.location.reload();
        } catch (error) {
            AlertManager.show('Erro ao revogar regulamento', 'danger');
        }
    }
}

// Inicializar quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new RegulationDetailManager();
});
// static/file_manager/js/regulation.js

class RegulationManager {
    constructor() {
        this.modal = document.getElementById('regulationModal');
        this.form = document.getElementById('regulationForm');
        this.saveBtn = document.getElementById('saveRegulationBtn');
        this.revokeModal = document.getElementById('revokeModal');
        this.confirmRevokeBtn = document.getElementById('confirmRevokeBtn');
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Salvar regulamento
        this.saveBtn?.addEventListener('click', () => this.handleSave());

        // Editar regulamento
        document.querySelectorAll('.edit-regulation').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleEdit(e));
        });

        // Revogar regulamento
        document.querySelectorAll('.revoke-regulation').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleRevoke(e));
        });

        // Confirmação de revogação
        this.confirmRevokeBtn?.addEventListener('click', () => this.confirmRevoke());
    }

    async handleSave() {
        try {
            const formData = new FormData(this.form);
            const regulationId = formData.get('regulation_id');
            const url = regulationId ? 
                `/file-manager/api/regulations/${regulationId}/` : 
                '/file-manager/api/regulations/';

            const response = await ApiClient.request(url, {
                method: regulationId ? 'PUT' : 'POST',
                body: JSON.stringify(Object.fromEntries(formData))
            });

            AlertManager.show('Regulamento salvo com sucesso!', 'success');
            this.closeModal();
            window.location.reload();
        } catch (error) {
            AlertManager.show('Erro ao salvar regulamento', 'danger');
        }
    }

    async handleEdit(event) {
        const regulationId = event.target.dataset.regulationId;
        try {
            const regulation = await ApiClient.request(`/file-manager/api/regulations/${regulationId}/`);
            this.populateForm(regulation);
            this.openModal();
        } catch (error) {
            AlertManager.show('Erro ao carregar dados do regulamento', 'danger');
        }
    }

    async handleRevoke(event) {
        const regulationId = event.target.dataset.regulationId;
        this.currentRegulationId = regulationId;
        new bootstrap.Modal(this.revokeModal).show();
    }

    async confirmRevoke() {
        try {
            await ApiClient.request(`/file-manager/api/regulations/${this.currentRegulationId}/revoke/`, {
                method: 'POST'
            });
            AlertManager.show('Regulamento revogado com sucesso!', 'success');
            window.location.reload();
        } catch (error) {
            AlertManager.show('Erro ao revogar regulamento', 'danger');
        }
    }

    populateForm(regulation) {
        Object.keys(regulation).forEach(key => {
            const input = this.form.elements[key];
            if (input) {
                input.value = regulation[key];
            }
        });
    }

    openModal() {
        const modalInstance = new bootstrap.Modal(this.modal);
        modalInstance.show();
    }

    closeModal() {
        const modalInstance = bootstrap.Modal.getInstance(this.modal);
        modalInstance?.hide();
    }
}

// Inicializar quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new RegulationManager();
});
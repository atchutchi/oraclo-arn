// Funcionalidade de Mensagens
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss para alertas
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }, 3000);
    });
});
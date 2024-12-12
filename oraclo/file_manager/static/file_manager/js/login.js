// file_manager/static/file_manager/js/login.js

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        // Adiciona classe de foco aos inputs
        const inputs = loginForm.querySelectorAll('input');
        
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.closest('.input-group').classList.add('input-group-focus');
            });
            
            input.addEventListener('blur', function() {
                this.closest('.input-group').classList.remove('input-group-focus');
            });
        });

        // Validação básica do formulário
        loginForm.addEventListener('submit', function(e) {
            const username = loginForm.querySelector('input[name="username"]').value;
            const password = loginForm.querySelector('input[name="password"]').value;
            
            if (!username.trim() || !password.trim()) {
                e.preventDefault();
                const alert = document.createElement('div');
                alert.className = 'alert alert-danger';
                alert.innerHTML = '<i class="fas fa-exclamation-circle"></i>Por favor, preencha todos os campos.';
                
                // Remove alertas anteriores
                loginForm.querySelectorAll('.alert').forEach(el => el.remove());
                
                // Adiciona novo alerta
                loginForm.insertBefore(alert, loginForm.firstChild);
            }
        });
    }
});
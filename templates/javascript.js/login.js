// login.js - SEM reCAPTCHA
const API_BASE_URL = window.location.origin + '/api';

// ============================================================
// CSRF TOKEN
// ============================================================
async function obterCsrfToken() {
    try {
        const response = await fetch(`${API_BASE_URL}/config/csrf-token`);
        const data = await response.json();
        document.getElementById('csrf-token').value = data.csrf_token || '';
    } catch (error) {
        console.error('Erro ao obter CSRF token:', error);
    }
}

// ============================================================
// MOSTRAR/OCULTAR SENHA
// ============================================================
function togglePassword() {
    const senhaInput = document.getElementById('senha');
    const icon = document.querySelector('.toggle-password i');
    if (senhaInput.type === 'password') {
        senhaInput.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        senhaInput.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

// ============================================================
// MOSTRAR MENSAGENS
// ============================================================
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    document.getElementById('successMessage').style.display = 'none';
    setTimeout(() => { errorDiv.style.display = 'none'; }, 5000);
}

function showSuccess(message) {
    const successDiv = document.getElementById('successMessage');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    document.getElementById('errorMessage').style.display = 'none';
    setTimeout(() => { successDiv.style.display = 'none'; }, 5000);
}

// ============================================================
// VERIFICAR SE JÁ ESTÁ LOGADO
// ============================================================
function verificarSessao() {
    const token = localStorage.getItem('token');
    const userType = localStorage.getItem('userType');

    if (token && userType) {
        if (userType === 'ong') {
            window.location.href = '/dashboard_ong.html';
        } else if (userType === 'admin') {
            window.location.href = '/admin_plataform.html';
        } else {
            window.location.href = '/';
        }
        return true;
    }
    return false;
}

// ============================================================
// LOGIN
// ============================================================
document.addEventListener('DOMContentLoaded', async () => {
    // Verificar se já está logado
    if (verificarSessao()) return;

    // Carregar CSRF token
    await obterCsrfToken();

    // Form submit
    const form = document.getElementById('login-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('email').value.trim();
        const senha = document.getElementById('senha').value;
        const tipo = document.getElementById('tipo').value;

        if (!email) {
            showError('Digite seu e-mail');
            return;
        }

        if (!senha) {
            showError('Digite sua senha');
            return;
        }

        const submitBtn = e.target.querySelector('button[type="submit"]');
        const textoOriginal = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Entrando...';
        submitBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': document.getElementById('csrf-token').value
                },
                body: JSON.stringify({
                    email,
                    senha,
                    tipo
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Erro no login');
            }

            if (data.token) {
                localStorage.setItem('token', data.token);
                localStorage.setItem('user', JSON.stringify(data.usuario));
                localStorage.setItem('userType', data.tipo);

                showSuccess('Login realizado com sucesso!');

                setTimeout(() => {
                    if (data.tipo === 'ong') {
                        window.location.href = '/dashboard_ong.html';
                    } else if (data.tipo === 'admin') {
                        window.location.href = '/admin_plataform.html';
                    } else {
                        window.location.href = '/';
                    }
                }, 1000);
            }
        } catch (error) {
            showError(error.message);
            submitBtn.innerHTML = textoOriginal;
            submitBtn.disabled = false;
        }
    });

    // Enter para submit
    document.getElementById('email').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') form.dispatchEvent(new Event('submit'));
    });

    document.getElementById('senha').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') form.dispatchEvent(new Event('submit'));
    });
});
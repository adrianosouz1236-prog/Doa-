function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = toast.querySelector('.toast-message');
    
    toastMessage.textContent = message;
    toast.className = `toast toast-${type}`;
    toast.style.display = 'block';
    
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

const API_BASE_URL = window.location.origin + '/api';

document.addEventListener('DOMContentLoaded', () => {
    // Verificar se já está logado
    const token = localStorage.getItem('token');
    const userType = localStorage.getItem('userType');
    
    if (token && userType) {
        // Se já estiver logado, redirecionar para o painel correto
        if (userType === 'ong') {
            window.location.href = '/dashboard_ong.html';
        } else if (userType === 'admin') {
            window.location.href = '/admin_plataform.html';
        } else if (userType === 'doador') {
            window.location.href = '/';
        }
        return;
    }
    
    const form = document.getElementById('login-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const senha = document.getElementById('senha').value;
            const tipo = document.getElementById('tipo').value;
            
            const submitBtn = e.target.querySelector('button[type="submit"]');
            const textoOriginal = submitBtn.textContent;
            submitBtn.textContent = 'Entrando...';
            submitBtn.disabled = true;
            
            try {
                console.log('📡 Tentando login:', { email, tipo });
                
                const response = await fetch(`${API_BASE_URL}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, senha, tipo })
                });
                
                const data = await response.json();
                console.log('📥 Resposta do servidor:', data);
                
                if (!response.ok) {
                    throw new Error(data.error || 'Erro no login');
                }
                
                if (data.token) {
                    localStorage.setItem('token', data.token);
                    localStorage.setItem('user', JSON.stringify(data.usuario));
                    localStorage.setItem('userType', data.tipo);
                    
                    showToast('Login realizado com sucesso!', 'success');
                    
                    // Redirecionar baseado no tipo de usuário
                    setTimeout(() => {
                        if (data.tipo === 'ong') {
                            console.log('🔀 Redirecionando para dashboard_ong.html');
                            window.location.href = '/dashboard_ong.html';
                        } else if (data.tipo === 'admin') {
                            console.log('🔀 Redirecionando para admin_plataform.html');
                            window.location.href = '/admin_plataform.html';
                        } else {
                            console.log('🔀 Redirecionando para /');
                            window.location.href = '/';
                        }
                    }, 1000);
                }
                
            } catch (error) {
                console.error('❌ Erro no login:', error);
                showToast(error.message, 'error');
            } finally {
                submitBtn.textContent = textoOriginal;
                submitBtn.disabled = false;
            }
        });
    }
});
const API_BASE_URL = window.location.origin + '/api';

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = toast.querySelector('.toast-message');
    toastMessage.textContent = message;
    toast.className = `toast toast-${type}`;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3000);
}

function getToken() { return localStorage.getItem('token'); }

function getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    const token = getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

async function apiRequest(endpoint, options = {}) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: getHeaders()
    });
    const data = await response.json();
    if (!response.ok) {
        if (response.status === 401) {
            localStorage.clear();
            window.location.href = '/login.html';
        }
        throw new Error(data.error || 'Erro na requisição');
    }
    return data;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== AUTENTICAÇÃO ====================
function updateAuthUI() {
    const token = getToken();
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    const navButtons = document.getElementById('nav-buttons');
    const userMenu = document.getElementById('user-menu');
    const userNameSpan = document.getElementById('user-name');

    if (token && user) {
        if (navButtons) navButtons.style.display = 'none';
        if (userMenu) {
            userMenu.style.display = 'flex';
            if (userNameSpan) userNameSpan.textContent = user.nome?.split(' ')[0] || 'Usuário';
        }
    } else {
        if (navButtons) navButtons.style.display = 'flex';
        if (userMenu) userMenu.style.display = 'none';
    }
}

function setupAuth() {
    updateAuthUI();
    
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.clear();
            window.location.href = '/';
        });
    }

    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('nav-menu');
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }
}

// ==================== FEEDBACK ====================
async function enviarFeedback(e) {
    e.preventDefault();
    
    const token = getToken();
    if (!token) {
        showToast('Faça login para enviar feedback', 'warning');
        window.location.href = '/login.html';
        return;
    }

    const mensagem = document.getElementById('feedback-mensagem').value;
    const tipo = document.getElementById('feedback-tipo').value;
    const anonimo = document.getElementById('feedback-anonimo').checked;

    if (!mensagem || mensagem.length < 3) {
        showToast('Mensagem deve ter pelo menos 3 caracteres', 'error');
        return;
    }

    const submitBtn = e.target.querySelector('button[type="submit"]');
    const textoOriginal = submitBtn.textContent;
    submitBtn.textContent = 'Enviando...';
    submitBtn.disabled = true;

    try {
        await apiRequest('/feedback', {
            method: 'POST',
            body: JSON.stringify({ mensagem, tipo, anonimo })
        });
        
        showToast('Feedback enviado com sucesso!', 'success');
        document.getElementById('feedback-form').reset();
        carregarMeusFeedbacks();
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.textContent = textoOriginal;
        submitBtn.disabled = false;
    }
}

async function carregarMeusFeedbacks() {
    const container = document.getElementById('meus-feedbacks-container');
    const token = getToken();
    
    if (!token) {
        container.innerHTML = '<p class="empty-state">Faça login para ver seus feedbacks</p>';
        return;
    }

    try {
        const data = await apiRequest('/feedback/meus');
        const feedbacks = data.feedbacks || [];

        if (feedbacks.length === 0) {
            container.innerHTML = '<p class="empty-state">Você ainda não enviou nenhum feedback</p>';
            return;
        }

        container.innerHTML = feedbacks.map(fb => {
            const dataEnvio = new Date(fb.data);
            const statusClass = fb.status === 'respondido' ? 'respondido' : 'pendente';
            const statusText = fb.status === 'respondido' ? '✅ Respondido' : '⏳ Pendente';
            
            return `
                <div class="feedback-item">
                    <div class="feedback-header">
                        <span class="feedback-tipo">${fb.tipo}</span>
                        <span class="feedback-status ${statusClass}">${statusText}</span>
                        <span class="feedback-data">${dataEnvio.toLocaleDateString('pt-BR')}</span>
                    </div>
                    <p class="feedback-mensagem">${escapeHtml(fb.mensagem)}</p>
                    ${fb.resposta ? `
                        <div class="feedback-resposta">
                            <strong>📌 Resposta:</strong>
                            <p>${escapeHtml(fb.resposta)}</p>
                            <small>${fb.data_resposta ? new Date(fb.data_resposta).toLocaleDateString('pt-BR') : ''}</small>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');

    } catch (error) {
        container.innerHTML = `<p class="error-state">Erro ao carregar feedbacks: ${error.message}</p>`;
    }
}

// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', () => {
    setupAuth();
    carregarMeusFeedbacks();

    const form = document.getElementById('feedback-form');
    if (form) {
        form.addEventListener('submit', enviarFeedback);
    }
});
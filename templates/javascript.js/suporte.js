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

// ==================== SUPORTE ====================
async function enviarSuporte(e) {
    e.preventDefault();
    
    const token = getToken();
    if (!token) {
        showToast('Faça login para abrir um chamado', 'warning');
        window.location.href = '/login.html';
        return;
    }

    const assunto = document.getElementById('suporte-assunto').value;
    const mensagem = document.getElementById('suporte-mensagem').value;
    const categoria = document.getElementById('suporte-categoria').value;

    if (!assunto || assunto.length < 3) {
        showToast('Assunto deve ter pelo menos 3 caracteres', 'error');
        return;
    }

    if (!mensagem || mensagem.length < 5) {
        showToast('Mensagem deve ter pelo menos 5 caracteres', 'error');
        return;
    }

    const submitBtn = e.target.querySelector('button[type="submit"]');
    const textoOriginal = submitBtn.textContent;
    submitBtn.textContent = 'Enviando...';
    submitBtn.disabled = true;

    try {
        await apiRequest('/suporte', {
            method: 'POST',
            body: JSON.stringify({ assunto, mensagem, categoria })
        });
        
        showToast('Solicitação de suporte enviada com sucesso!', 'success');
        document.getElementById('suporte-form').reset();
        carregarMeusSuportes();
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.textContent = textoOriginal;
        submitBtn.disabled = false;
    }
}

async function carregarMeusSuportes() {
    const container = document.getElementById('meus-suportes-container');
    const token = getToken();
    
    if (!token) {
        container.innerHTML = '<p class="empty-state">Faça login para ver seus chamados</p>';
        return;
    }

    try {
        const data = await apiRequest('/suporte/meus');
        const suportes = data.suportes || [];

        if (suportes.length === 0) {
            container.innerHTML = '<p class="empty-state">Você ainda não abriu nenhum chamado</p>';
            return;
        }

        container.innerHTML = suportes.map(sp => {
            const dataEnvio = new Date(sp.data);
            const statusMap = {
                'aberto': '🟡 Aberto',
                'em_andamento': '🟠 Em Andamento',
                'resolvido': '🟢 Resolvido',
                'fechado': '⚫ Fechado'
            };
            const statusText = statusMap[sp.status] || sp.status;
            const statusClass = sp.status;
            
            return `
                <div class="suporte-item">
                    <div class="suporte-header">
                        <span class="suporte-categoria">${sp.categoria}</span>
                        <span class="suporte-status ${statusClass}">${statusText}</span>
                        <span class="suporte-data">${dataEnvio.toLocaleDateString('pt-BR')}</span>
                    </div>
                    <h4 class="suporte-assunto">${escapeHtml(sp.assunto)}</h4>
                    <p class="suporte-mensagem">${escapeHtml(sp.mensagem)}</p>
                    ${sp.resposta ? `
                        <div class="suporte-resposta">
                            <strong>📌 Resposta:</strong>
                            <p>${escapeHtml(sp.resposta)}</p>
                            <small>${sp.data_resposta ? new Date(sp.data_resposta).toLocaleDateString('pt-BR') : ''}</small>
                        </div>
                    ` : `
                        <div class="suporte-aguardando">
                            <small>⏳ Aguardando resposta da equipe de suporte</small>
                        </div>
                    `}
                </div>
            `;
        }).join('');

    } catch (error) {
        container.innerHTML = `<p class="error-state">Erro ao carregar chamados: ${error.message}</p>`;
    }
}

// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', () => {
    setupAuth();
    carregarMeusSuportes();

    const form = document.getElementById('suporte-form');
    if (form) {
        form.addEventListener('submit', enviarSuporte);
    }
});
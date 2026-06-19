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

// ==================== CENTRAL DE AJUDA ====================
let artigosData = [];
let categoriaAtual = 'todos';

async function carregarArtigos(categoria = 'todos') {
    const container = document.getElementById('artigos-container');
    
    try {
        const params = categoria !== 'todos' ? `?categoria=${categoria}` : '';
        const data = await apiRequest(`/ajuda${params}`);
        artigosData = data.artigos || [];

        if (artigosData.length === 0) {
            container.innerHTML = '<p class="empty-state">Nenhum artigo encontrado para esta categoria</p>';
            return;
        }

        container.innerHTML = artigosData.map(artigo => {
            const categoriaIcon = {
                'geral': '📌',
                'doador': '🤝',
                'ong': '🏢',
                'suporte': '🆘',
                'feedback': '📝'
            };
            const icon = categoriaIcon[artigo.categoria] || '📄';
            
            return `
                <div class="artigo-card" onclick="toggleArtigo(${artigo.id})">
                    <div class="artigo-header">
                        <span class="artigo-icon">${icon}</span>
                        <span class="artigo-categoria">${artigo.categoria}</span>
                        <h3 class="artigo-titulo">${escapeHtml(artigo.titulo)}</h3>
                    </div>
                    <div class="artigo-conteudo" id="artigo-${artigo.id}" style="display: none;">
                        <p>${escapeHtml(artigo.conteudo).replace(/\n/g, '<br>')}</p>
                    </div>
                </div>
            `;
        }).join('');

    } catch (error) {
        container.innerHTML = `<p class="error-state">Erro ao carregar artigos: ${error.message}</p>`;
    }
}

function toggleArtigo(id) {
    const conteudo = document.getElementById(`artigo-${id}`);
    if (conteudo) {
        const isVisible = conteudo.style.display !== 'none';
        conteudo.style.display = isVisible ? 'none' : 'block';
        
        // Animação suave
        if (!isVisible) {
            conteudo.style.animation = 'slideDown 0.3s ease';
        }
    }
}

function setupFilters() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            categoriaAtual = btn.dataset.categoria;
            carregarArtigos(categoriaAtual);
        });
    });
}

// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', () => {
    setupAuth();
    carregarArtigos('todos');
    setupFilters();
});
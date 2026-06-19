// ==================== CONFIGURAÇÃO DA API ====================
const API_BASE_URL = window.location.origin + '/api';

// ==================== FUNÇÕES AUXILIARES ====================
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    const toastMessage = toast.querySelector('.toast-message');
    toastMessage.textContent = message;
    toast.className = `toast toast-${type}`;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getToken() {
    return localStorage.getItem('token');
}

function getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    const token = getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

// ==================== API ====================
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    console.log(`📡 ${options.method || 'GET'}:`, url);
    
    try {
        const response = await fetch(url, {
            ...options,
            headers: getHeaders()
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.clear();
                window.location.href = '/login.html';
                throw new Error('Sua sessão expirou. Faça login novamente.');
            }
            throw new Error(data.error || 'Erro na requisição');
        }
        
        console.log('✅ Resposta:', data);
        return data;
    } catch (error) {
        console.error('❌ Erro:', error);
        throw error;
    }
}

// ==================== FUNÇÕES DA API ====================
async function obterEstatisticas() {
    return apiRequest('/dashboard/stats');
}

async function listarNecessidades(filtros = {}) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filtros)) {
        if (value && value !== '' && value !== 'all') {
            params.append(key, value);
        }
    }
    const queryString = params.toString();
    return apiRequest(`/necessidades${queryString ? '?' + queryString : ''}`);
}

async function listarEventos() {
    return apiRequest('/eventos');
}

async function registrarDoacao(dados) {
    return apiRequest('/doacoes', {
        method: 'POST',
        body: JSON.stringify(dados)
    });
}

// ==================== AUTENTICAÇÃO ====================
const auth = {
    isAuthenticated: !!localStorage.getItem('token'),
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    userType: localStorage.getItem('userType'),

    updateUI() {
        const navButtons = document.getElementById('nav-buttons');
        const userMenu = document.getElementById('user-menu');
        const userNameSpan = document.getElementById('user-name');

        if (this.isAuthenticated && this.user) {
            if (navButtons) navButtons.style.display = 'none';
            if (userMenu) {
                userMenu.style.display = 'flex';
                if (userNameSpan) userNameSpan.textContent = this.user.nome?.split(' ')[0] || 'Usuário';
            }
        } else {
            if (navButtons) navButtons.style.display = 'flex';
            if (userMenu) userMenu.style.display = 'none';
        }
    },

    setup() {
        this.updateUI();
        
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                localStorage.clear();
                this.isAuthenticated = false;
                this.user = null;
                this.userType = null;
                this.updateUI();
                showToast('Você saiu do sistema', 'info');
                setTimeout(() => { window.location.href = '/'; }, 500);
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
};

// ==================== VARIÁVEIS GLOBAIS ====================
let currentPage = 1;
let isLoading = false;
let hasMore = true;
let currentFilters = { cidade: '', categoria: '', status: 'all' };

// ==================== CARREGAR DADOS ====================
async function carregarEstatisticas() {
    try {
        const stats = await obterEstatisticas();
        console.log('📊 Estatísticas:', stats);
        
        document.getElementById('stat-ongs').textContent = stats.total_ongs || 0;
        document.getElementById('stat-doacoes').textContent = stats.total_doacoes || 0;
        document.getElementById('stat-itens').textContent = stats.total_itens || 0;
    } catch (error) {
        console.error('❌ Erro ao carregar estatísticas:', error);
    }
}

async function carregarEventos() {
    const container = document.getElementById('eventos-container');
    if (!container) {
        console.warn('⚠️ Container de eventos não encontrado');
        return;
    }

    try {
        const data = await listarEventos();
        console.log('📦 Eventos recebidos:', data);
        const eventos = data.eventos || [];

        if (eventos.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>Nenhum evento programado no momento.</p></div>';
            return;
        }

        container.innerHTML = eventos.map(evento => {
            const dataEvento = new Date(evento.data_evento);
            const dataFormatada = dataEvento.toLocaleDateString('pt-BR');
            const horaFormatada = dataEvento.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
            
            return `
                <div class="evento-card" onclick="window.location.href='/perfil_ong.html?id=${evento.ong_id}'">
                    <img class="evento-imagem" src="${evento.imagem_url || 'https://via.placeholder.com/400x200?text=Evento'}" alt="${escapeHtml(evento.titulo)}">
                    <h3>${escapeHtml(evento.titulo)}</h3>
                    <div class="evento-data">📅 ${dataFormatada} • ${horaFormatada}</div>
                    <div class="evento-local">📍 ${escapeHtml(evento.local_evento || evento.cidade || 'Local não informado')}</div>
                    <p class="evento-descricao">${escapeHtml(evento.descricao?.substring(0, 100))}${evento.descricao?.length > 100 ? '...' : ''}</p>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('❌ Erro ao carregar eventos:', error);
        container.innerHTML = `<div class="error-message"><p>Erro ao carregar eventos: ${error.message}</p></div>`;
    }
}

async function carregarNecessidades(append = false) {
    if (isLoading) return;
    isLoading = true;
    
    const container = document.getElementById('necessidades-container');
    if (!container) {
        console.warn('⚠️ Container de necessidades não encontrado');
        isLoading = false;
        return;
    }

    if (!append) {
        container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Carregando necessidades...</p></div>';
    }

    try {
        const params = {
            cidade: currentFilters.cidade || '',
            categoria: currentFilters.categoria || '',
            page: currentPage,
            limit: 10
        };
        if (currentFilters.status === 'urgente') params.urgente = 'true';

        console.log('🔍 Buscando necessidades com params:', params);
        const data = await listarNecessidades(params);
        console.log('📦 Necessidades recebidas:', data);
        const necessidades = data.necessidades || [];
        
        hasMore = data.has_more || false;

        if (!append) {
            renderizarNecessidades(necessidades);
        } else {
            adicionarNecessidades(necessidades);
        }

        const loadMoreBtn = document.getElementById('btn-load-more');
        if (loadMoreBtn) {
            loadMoreBtn.style.display = hasMore ? 'block' : 'none';
        }
    } catch (error) {
        console.error('❌ Erro ao carregar necessidades:', error);
        if (!append) {
            container.innerHTML = `<div class="error-message"><p>Erro ao carregar: ${error.message}</p><button onclick="location.reload()" class="btn btn-secondary">Tentar Novamente</button></div>`;
        }
    } finally {
        isLoading = false;
    }
}

function renderizarNecessidades(necessidades) {
    const container = document.getElementById('necessidades-container');
    if (!container) return;

    if (!necessidades || necessidades.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>🎯 Nenhuma necessidade encontrada</h3><p>Tente ajustar os filtros de busca.</p></div>';
        return;
    }

    container.innerHTML = necessidades.map(nec => criarCardHtml(nec)).join('');
    
    document.querySelectorAll('.btn-doar').forEach(btn => {
        btn.addEventListener('click', () => abrirModalDoacao(btn.dataset.id));
    });
    
    document.querySelectorAll('.ong-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.stopPropagation();
            window.location.href = `/perfil_ong.html?id=${link.dataset.ongId}`;
        });
    });
}

function criarCardHtml(nec) {
    const percentual = nec.quantidade_necessaria > 0 
        ? Math.min((nec.quantidade_recebida / nec.quantidade_necessaria) * 100, 100)
        : 0;
    const statusClass = nec.urgencia === 'alta' ? 'urgent' : '';
    
    return `
        <div class="card ${statusClass}">
            ${nec.urgencia === 'alta' ? '<span class="badge-urgente">URGENTE</span>' : ''}
            <h3>${escapeHtml(nec.titulo)}</h3>
            <p class="ong ong-link" data-ong-id="${nec.ong_id}" style="cursor: pointer;">🏢 ${escapeHtml(nec.ong_nome)}</p>
            <p class="endereco">📍 ${escapeHtml(nec.cidade || 'Local não informado')}</p>
            <p class="descricao">${escapeHtml(nec.descricao || '')}</p>
            <div class="progress-section">
                <div class="progress-bar">
                    <div class="progress" style="width: ${percentual}%"></div>
                </div>
                <p class="quantidade">${nec.quantidade_recebida || 0} / ${nec.quantidade_necessaria} itens</p>
            </div>
            <button class="btn-doar" data-id="${nec.id}">Quero Doar</button>
        </div>
    `;
}

function adicionarNecessidades(necessidades) {
    const container = document.getElementById('necessidades-container');
    const html = necessidades.map(nec => criarCardHtml(nec)).join('');
    container.insertAdjacentHTML('beforeend', html);
    
    document.querySelectorAll('.btn-doar').forEach(btn => {
        btn.addEventListener('click', () => abrirModalDoacao(btn.dataset.id));
    });
    
    document.querySelectorAll('.ong-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.stopPropagation();
            window.location.href = `/perfil_ong.html?id=${link.dataset.ongId}`;
        });
    });
}

// ==================== MODAL DE DOAÇÃO ====================
function abrirModalDoacao(necessidadeId) {
    if (!auth.isAuthenticated) {
        showToast('Faça login para realizar uma doação', 'warning');
        setTimeout(() => { window.location.href = '/login.html'; }, 1500);
        return;
    }

    document.getElementById('modal-necessidade-id').value = necessidadeId;
    document.getElementById('modal-quantidade').value = 1;
    document.getElementById('modal-mensagem').value = '';
    document.getElementById('doacao-modal').style.display = 'flex';
}

function fecharModal() {
    document.getElementById('doacao-modal').style.display = 'none';
}

async function handleDoacaoSubmit(e) {
    e.preventDefault();
    
    const necessidadeId = document.getElementById('modal-necessidade-id').value;
    const quantidade = parseInt(document.getElementById('modal-quantidade').value);
    const mensagem = document.getElementById('modal-mensagem').value;

    if (!quantidade || quantidade < 1) {
        showToast('Informe uma quantidade válida', 'error');
        return;
    }

    const submitBtn = e.target.querySelector('button[type="submit"]');
    const textoOriginal = submitBtn.textContent;
    submitBtn.textContent = 'Processando...';
    submitBtn.disabled = true;

    try {
        await registrarDoacao({ necessidade_id: necessidadeId, quantidade, mensagem });
        showToast('Doação registrada com sucesso!', 'success');
        fecharModal();
        currentPage = 1;
        carregarNecessidades();
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.textContent = textoOriginal;
        submitBtn.disabled = false;
    }
}

// ==================== CONTROLES ====================
async function loadMore() {
    if (!hasMore || isLoading) return;
    currentPage++;
    await carregarNecessidades(true);
}

function handleSearch() {
    currentFilters.cidade = document.getElementById('search-cidade')?.value || '';
    currentFilters.categoria = document.getElementById('search-categoria')?.value || '';
    currentPage = 1;
    hasMore = true;
    carregarNecessidades();
}

function configurarEventos() {
    const btnBuscar = document.getElementById('btn-buscar');
    const searchCidade = document.getElementById('search-cidade');
    const searchCategoria = document.getElementById('search-categoria');
    const btnLoadMore = document.getElementById('btn-load-more');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const modal = document.getElementById('doacao-modal');
    const closeBtn = document.querySelector('.modal-close');
    const formDoacao = document.getElementById('form-doacao');

    if (btnBuscar) btnBuscar.addEventListener('click', handleSearch);
    if (btnLoadMore) btnLoadMore.addEventListener('click', loadMore);
    if (searchCidade) searchCidade.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSearch(); });
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilters.status = btn.dataset.filter;
            currentPage = 1;
            hasMore = true;
            carregarNecessidades();
        });
    });

    if (closeBtn) closeBtn.addEventListener('click', fecharModal);
    if (modal) window.addEventListener('click', (e) => { if (e.target === modal) fecharModal(); });
    if (formDoacao) formDoacao.addEventListener('submit', handleDoacaoSubmit);
}

// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Página carregada!');
    console.log('🔑 Token:', getToken() ? 'Presente' : 'Ausente');
    
    auth.setup();
    carregarEstatisticas();
    carregarEventos();
    carregarNecessidades();
    configurarEventos();
});

// Exportar funções para uso global
window.carregarNecessidades = carregarNecessidades;
window.carregarEventos = carregarEventos;
window.carregarEstatisticas = carregarEstatisticas;
window.loadMore = loadMore;
window.handleSearch = handleSearch;
window.abrirModalDoacao = abrirModalDoacao;
window.fecharModal = fecharModal;
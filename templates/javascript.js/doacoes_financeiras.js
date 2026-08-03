const API_BASE_URL = window.location.origin + '/api';
let csrfToken = '';

async function obterCsrfToken() {
    try {
        const response = await fetch(`${API_BASE_URL}/config/csrf-token`);
        const data = await response.json();
        csrfToken = data.csrf_token || '';
        document.getElementById('csrf-token').value = csrfToken;
    } catch (error) {
        console.error('Erro ao obter CSRF token:', error);
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = toast.querySelector('.toast-message');
    toastMessage.textContent = message;
    toast.className = `toast toast-${type}`;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3000);
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
    headers['X-CSRF-Token'] = csrfToken;
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

function updateAuthUI() {
    const token = getToken();
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    const userMenu = document.getElementById('user-menu');
    const userNameSpan = document.getElementById('user-name');

    if (token && user) {
        if (userMenu) {
            userMenu.style.display = 'flex';
            if (userNameSpan) userNameSpan.textContent = user.nome?.split(' ')[0] || 'Usuário';
        }
    } else {
        if (userMenu) userMenu.style.display = 'none';
        window.location.href = '/login.html';
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
}

async function carregarOngs() {
    try {
        const data = await apiRequest('/ongs');
        const ongs = data.ongs || [];
        const select = document.getElementById('ong-select');
        select.innerHTML = '<option value="">Selecione uma ONG</option>' +
            ongs.map(ong => `<option value="${ong.id}">${escapeHtml(ong.nome)} - ${escapeHtml(ong.cidade)}</option>`).join('');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function setValor(valor) {
    document.getElementById('valor-doacao').value = valor;
}

async function enviarDoacaoFinanceira(e) {
    e.preventDefault();
    const token = getToken();
    if (!token) {
        showToast('Faça login para doar', 'warning');
        window.location.href = '/login.html';
        return;
    }
    const ongId = document.getElementById('ong-select').value;
    const valor = parseFloat(document.getElementById('valor-doacao').value);
    const mensagem = document.getElementById('mensagem-doacao').value;
    const metodoPagamento = document.getElementById('metodo-pagamento').value;
    const recorrente = document.getElementById('doacao-recorrente').checked;
    if (!ongId) { showToast('Selecione uma ONG', 'error'); return; }
    if (!valor || valor < 1) { showToast('Valor mínimo é R$ 1,00', 'error'); return; }
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const textoOriginal = submitBtn.textContent;
    submitBtn.textContent = 'Processando...';
    submitBtn.disabled = true;
    try {
        const data = await apiRequest('/doacoes/financeiras/criar', {
            method: 'POST',
            body: JSON.stringify({
                ong_id: parseInt(ongId),
                valor: valor,
                mensagem: mensagem,
                metodo_pagamento: metodoPagamento,
                recorrente: recorrente
            })
        });
        showToast(`💰 Doação de R$ ${valor.toFixed(2)} realizada com sucesso!`, 'success');
        document.getElementById('form-doacao-financeira').reset();
        carregarMinhasDoacoes();
        carregarEstatisticas();
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.textContent = textoOriginal;
        submitBtn.disabled = false;
    }
}

async function carregarMinhasDoacoes() {
    const container = document.getElementById('minhas-doacoes-container');
    const token = getToken();
    if (!token) {
        container.innerHTML = '<p class="empty-state">Faça login para ver suas doações</p>';
        return;
    }
    try {
        const data = await apiRequest('/doacoes/financeiras/minhas');
        const doacoes = data.doacoes || [];
        if (doacoes.length === 0) {
            container.innerHTML = '<p class="empty-state">Você ainda não fez nenhuma doação financeira</p>';
            return;
        }
        container.innerHTML = doacoes.map(d => {
            const statusClass = d.status === 'confirmado' ? 'status-confirmado' : 'status-pendente';
            const statusText = d.status === 'confirmado' ? '✅ Confirmado' : '⏳ Pendente';
            return `
                <div class="doacao-item">
                    <div class="doacao-header">
                        <span class="doacao-ong">🏢 ${escapeHtml(d.ong_nome)}</span>
                        <span class="doacao-valor">R$ ${d.valor.toFixed(2)}</span>
                    </div>
                    <div class="doacao-detalhes">
                        <span>📅 ${new Date(d.data_criacao).toLocaleString()}</span>
                        <span class="doacao-metodo">${d.metodo_pagamento}</span>
                        ${d.recorrente ? '<span class="badge-recorrente">🔄 Recorrente</span>' : ''}
                        <span class="doacao-status ${statusClass}">${statusText}</span>
                    </div>
                    ${d.mensagem ? `<p class="doacao-mensagem">💬 ${escapeHtml(d.mensagem)}</p>` : ''}
                    ${d.transacao_id ? `<small class="doacao-transacao">ID: ${d.transacao_id}</small>` : ''}
                </div>
            `;
        }).join('');
    } catch (error) {
        container.innerHTML = `<p class="error-state">Erro ao carregar doações: ${error.message}</p>`;
    }
}

async function carregarEstatisticas() {
    const token = getToken();
    if (!token) return;
    try {
        const data = await apiRequest('/doacoes/financeiras/estatisticas');
        document.getElementById('total-doado').textContent = `R$ ${(data.total_valor || 0).toFixed(2)}`;
        document.getElementById('total-doacoes-financeiras').textContent = data.total_doacoes || 0;
        document.getElementById('media-doacao').textContent = `R$ ${(data.media_valor || 0).toFixed(2)}`;
        document.getElementById('doacoes-recorrentes').textContent = data.doacoes_recorrentes || 0;
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    await obterCsrfToken();
    setupAuth();
    carregarOngs();
    carregarMinhasDoacoes();
    carregarEstatisticas();
    const form = document.getElementById('form-doacao-financeira');
    if (form) {
        form.addEventListener('submit', enviarDoacaoFinanceira);
    }
});
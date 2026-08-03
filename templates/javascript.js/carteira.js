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
    const userType = localStorage.getItem('userType');
    const userNameSpan = document.getElementById('user-name');
    if (!token || userType !== 'ong') {
        window.location.href = '/login.html';
        return;
    }
    if (user && userNameSpan) {
        userNameSpan.textContent = user.nome?.split(' ')[0] || 'ONG';
    }
}

document.getElementById('logout-btn')?.addEventListener('click', () => {
    localStorage.clear();
    window.location.href = '/';
});

async function carregarSaldo() {
    try {
        const data = await apiRequest('/carteira/saldo');
        document.getElementById('saldo-disponivel').textContent = `R$ ${(data.saldo || 0).toFixed(2)}`;
        document.getElementById('total-recebido').textContent = `R$ ${(data.total_recebido || 0).toFixed(2)}`;
        document.getElementById('total-sacado').textContent = `R$ ${(data.total_sacado || 0).toFixed(2)}`;
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function carregarExtrato() {
    const container = document.getElementById('extrato-container');
    try {
        const data = await apiRequest('/carteira/extrato');
        const extrato = data.extrato || [];
        if (extrato.length === 0) {
            container.innerHTML = '<p class="empty-state">Nenhuma transação encontrada</p>';
            return;
        }
        container.innerHTML = extrato.map(t => {
            const tipoIcon = t.tipo === 'doacao_financeira' ? '💰 Entrada' : '💸 Saque';
            const tipoClass = t.tipo === 'doacao_financeira' ? 'entrada' : 'saida';
            const statusText = t.status === 'confirmado' ? '✅ Confirmado' : '⏳ Processando';
            return `
                <div class="transacao-item ${tipoClass}">
                    <div class="transacao-info">
                        <span class="transacao-tipo">${tipoIcon}</span>
                        <span class="transacao-id">${t.transacao_id}</span>
                    </div>
                    <div class="transacao-valor">
                        <span class="valor ${tipoClass}">${t.tipo === 'doacao_financeira' ? '+' : '-'} R$ ${t.valor.toFixed(2)}</span>
                        <span class="transacao-status">${statusText}</span>
                    </div>
                    <div class="transacao-data">
                        ${new Date(t.data_criacao).toLocaleString()}
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        container.innerHTML = `<p class="error-state">Erro ao carregar extrato: ${error.message}</p>`;
    }
}

async function carregarDoacoesRecebidas() {
    const container = document.getElementById('doacoes-recebidas-container');
    try {
        const data = await apiRequest('/doacoes/financeiras/ong');
        const doacoes = data.doacoes || [];
        if (doacoes.length === 0) {
            container.innerHTML = '<p class="empty-state">Nenhuma doação financeira recebida</p>';
            return;
        }
        container.innerHTML = doacoes.map(d => `
            <div class="doacao-item">
                <div class="doacao-header">
                    <span class="doacao-doador">👤 ${escapeHtml(d.doador_nome)}</span>
                    <span class="doacao-valor">R$ ${d.valor.toFixed(2)}</span>
                </div>
                <div class="doacao-detalhes">
                    <span>📅 ${new Date(d.data_criacao).toLocaleString()}</span>
                    <span>${d.metodo_pagamento}</span>
                    ${d.recorrente ? '<span class="badge-recorrente">🔄 Recorrente</span>' : ''}
                    <span class="doacao-status ${d.status === 'confirmado' ? 'status-confirmado' : 'status-pendente'}">
                        ${d.status === 'confirmado' ? '✅ Confirmado' : '⏳ Pendente'}
                    </span>
                </div>
                ${d.mensagem ? `<p class="doacao-mensagem">💬 ${escapeHtml(d.mensagem)}</p>` : ''}
            </div>
        `).join('');
    } catch (error) {
        container.innerHTML = `<p class="error-state">Erro ao carregar doações: ${error.message}</p>`;
    }
}

function abrirModalSaque() {
    document.getElementById('saque-modal').style.display = 'flex';
    document.getElementById('valor-saque').value = '';
    document.getElementById('conta-bancaria').value = '';
    apiRequest('/carteira/saldo').then(data => {
        if (data.conta_bancaria) {
            document.getElementById('conta-bancaria').value = data.conta_bancaria;
        }
    }).catch(error => console.error('Erro ao carregar conta:', error));
}

function fecharModalSaque() {
    document.getElementById('saque-modal').style.display = 'none';
}

document.getElementById('form-saque')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const valor = parseFloat(document.getElementById('valor-saque').value);
    const contaBancaria = document.getElementById('conta-bancaria').value;
    if (!valor || valor < 10) {
        showToast('Valor mínimo para saque é R$ 10,00', 'error');
        return;
    }
    if (!contaBancaria) {
        showToast('Informe a conta bancária', 'error');
        return;
    }
    try {
        await apiRequest('/carteira/sacar', {
            method: 'POST',
            body: JSON.stringify({ valor, conta_bancaria: contaBancaria })
        });
        showToast('Saque solicitado com sucesso!', 'success');
        fecharModalSaque();
        carregarSaldo();
        carregarExtrato();
    } catch (error) {
        showToast(error.message, 'error');
    }
});

document.addEventListener('DOMContentLoaded', async () => {
    await obterCsrfToken();
    updateAuthUI();
    carregarSaldo();
    carregarExtrato();
    carregarDoacoesRecebidas();
});
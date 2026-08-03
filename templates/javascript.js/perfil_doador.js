const API_BASE_URL = window.location.origin + '/api';
let csrfToken = '';
let userData = {};
let conquistasDisponiveis = [];
let doacoesFinanceiras = [];
let doacoesItens = [];

// ==================== TOAST ====================
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = toast.querySelector('.toast-message');
    toastMessage.textContent = message;
    toast.className = `toast toast-${type}`;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3000);
}

// ==================== CSRF TOKEN ====================
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

// ==================== AUTENTICAÇÃO ====================
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

// ==================== AUTH UI ====================
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

// ==================== FORÇA DA SENHA ====================
function validarSenhaForte(senha) {
    const requisitos = [];
    if (senha.length >= 12) requisitos.push('✅ 12+ caracteres');
    else requisitos.push('❌ 12+ caracteres');
    if (/[A-Z]/.test(senha)) requisitos.push('✅ Letra maiúscula');
    else requisitos.push('❌ Letra maiúscula');
    if (/[a-z]/.test(senha)) requisitos.push('✅ Letra minúscula');
    else requisitos.push('❌ Letra minúscula');
    if (/\d/.test(senha)) requisitos.push('✅ Número');
    else requisitos.push('❌ Número');
    if (/[!@#$%^&*(),.?":{}|<>]/.test(senha)) requisitos.push('✅ Caractere especial');
    else requisitos.push('❌ Caractere especial');
    return requisitos;
}

function atualizarForcaSenha(senha) {
    const container = document.getElementById('senha-forca');
    if (!container) return;
    if (!senha) {
        container.innerHTML = '';
        return;
    }
    const requisitos = validarSenhaForte(senha);
    const validos = requisitos.filter(r => r.startsWith('✅')).length;
    const total = requisitos.length;
    const porcentagem = (validos / total) * 100;
    let cor, texto;
    if (porcentagem === 100) { cor = '#27ae60'; texto = '🟢 Senha Forte'; }
    else if (porcentagem >= 60) { cor = '#f39c12'; texto = '🟡 Senha Média'; }
    else { cor = '#e74c3c'; texto = '🔴 Senha Fraca'; }
    container.innerHTML = `
        <div style="display: flex; flex-wrap: wrap; gap: 0.3rem; margin-bottom: 0.3rem;">
            ${requisitos.map(r => `<span style="font-size: 0.7rem; color: ${r.startsWith('✅') ? '#27ae60' : '#e74c3c'};">${r}</span>`).join('')}
        </div>
        <div style="width: 100%; height: 4px; background: #ecf0f1; border-radius: 2px; overflow: hidden;">
            <div style="width: ${porcentagem}%; height: 100%; background: ${cor}; transition: width 0.3s;"></div>
        </div>
        <span style="font-size: 0.8rem; color: ${cor}; font-weight: bold;">${texto}</span>
    `;
}

// ==================== CARREGAR DADOS DO PERFIL ====================
async function carregarPerfil() {
    try {
        const data = await apiRequest('/usuario/dados');
        userData = data.dados || {};
        
        document.getElementById('doador-nome').textContent = userData.nome || 'Doador';
        document.getElementById('doador-email').textContent = userData.email || '';
        document.getElementById('nome').value = userData.nome || '';
        document.getElementById('email').value = userData.email || '';
        document.getElementById('telefone').value = userData.telefone || '';
        document.getElementById('cpf').value = userData.cpf || '';
        document.getElementById('endereco').value = userData.endereco || '';
        document.getElementById('cidade').value = userData.cidade || '';
        document.getElementById('uf').value = userData.uf || '';
        
        document.getElementById('total-doacoes').textContent = userData.total_doacoes || 0;
        document.getElementById('pontuacao').textContent = userData.pontuacao || 0;
        document.getElementById('total-itens').textContent = userData.total_itens || 0;
        
        // Inicial da avatar
        const inicial = userData.nome?.charAt(0) || '👤';
        document.getElementById('avatar-inicial').textContent = inicial;
        
        // Carregar conquistas
        await carregarConquistas();
        
        // Carregar doações
        await carregarDoacoes();
        await carregarDoacoesFinanceiras();
        
        // Carregar status 2FA
        await carregarStatus2FA();
        
        // Carregar preferências de notificação
        await carregarPreferenciasNotificacoes();
        
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ==================== CONQUISTAS ====================
async function carregarConquistas() {
    const container = document.getElementById('conquistas-container');
    try {
        const data = await apiRequest('/doador/conquistas');
        const conquistas = data.conquistas || [];
        const todasConquistas = data.todas_conquistas || [];
        conquistasDisponiveis = todasConquistas;
        
        const desbloqueadas = conquistas.length;
        const total = todasConquistas.length;
        const progresso = total > 0 ? Math.round((desbloqueadas / total) * 100) : 0;
        
        document.getElementById('conquistas-desbloqueadas').textContent = desbloqueadas;
        document.getElementById('conquistas-total').textContent = total;
        document.getElementById('conquistas-progresso').textContent = `${progresso}%`;
        
        if (total === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>🚀 Você ainda não tem conquistas.</p>
                    <p style="font-size: 0.8rem; color: #7f8c8d;">Faça doações para desbloquear suas primeiras conquistas!</p>
                </div>
            `;
            return;
        }
        
        const icones = {
            'primeira_doacao': '🌟',
            'doador_frequente': '⭐',
            'doador_master': '🏆',
            '100_pontos': '💎',
            '500_pontos': '👑',
            '1000_pontos': '🔥'
        };
        
        const descricoes = {
            'primeira_doacao': 'Realizou sua primeira doação',
            'doador_frequente': 'Realizou 5 doações',
            'doador_master': 'Realizou 20 doações',
            '100_pontos': 'Acumulou 100 pontos',
            '500_pontos': 'Acumulou 500 pontos',
            '1000_pontos': 'Acumulou 1000 pontos'
        };
        
        container.innerHTML = todasConquistas.map(c => {
            const desbloqueada = conquistas.some(cq => cq === c.id);
            return `
                <div class="conquista-card ${desbloqueada ? '' : 'locked'}">
                    <span class="icone">${icones[c.id] || '🏅'}</span>
                    <span class="nome">${descricoes[c.id] || c.nome || 'Conquista'}</span>
                    <span class="descricao">${c.descricao || ''}</span>
                    ${desbloqueada ? '<span class="badge badge-success" style="font-size: 0.6rem;">✅ Desbloqueada</span>' : '<span class="badge badge-inactive" style="font-size: 0.6rem;">🔒 Bloqueada</span>'}
                </div>
            `;
        }).join('');
    } catch (error) {
        container.innerHTML = `<p class="error-state">Erro: ${error.message}</p>`;
    }
}

// ==================== DOAÇÕES (ITENS) ====================
async function carregarDoacoes() {
    const tbody = document.getElementById('doacoes-tbody');
    try {
        const data = await apiRequest('/doacoes/minhas');
        const doacoes = data.doacoes || [];
        doacoesItens = doacoes;
        
        if (doacoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">Nenhuma doação realizada</td></tr>';
            return;
        }
        
        tbody.innerHTML = doacoes.map(d => {
            const statusClass = d.status === 'confirmada' ? 'badge-success' : 'badge-warning';
            const statusText = d.status === 'confirmada' ? '✅ Confirmada' : '⏳ Pendente';
            return `
                <tr>
                    <td>${new Date(d.data).toLocaleDateString('pt-BR')}</td>
                    <td>${d.ong_nome || 'Desconhecida'}</td>
                    <td>${d.item || 'Item não informado'}</td>
                    <td>${d.quantidade}</td>
                    <td><span class="badge ${statusClass}">${statusText}</span></td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #e74c3c;">Erro: ${error.message}</td></tr>`;
    }
}

// ==================== DOAÇÕES FINANCEIRAS ====================
async function carregarDoacoesFinanceiras() {
    const tbody = document.getElementById('financeiras-tbody');
    try {
        const data = await apiRequest('/doacoes/financeiras/minhas');
        const doacoes = data.doacoes || [];
        doacoesFinanceiras = doacoes;
        
        const total = doacoes.filter(d => d.status === 'confirmado').reduce((sum, d) => sum + d.valor, 0);
        const count = doacoes.filter(d => d.status === 'confirmado').length;
        const media = count > 0 ? total / count : 0;
        const recorrentes = doacoes.filter(d => d.recorrente).length;
        
        document.getElementById('financeiro-total').textContent = `R$ ${total.toFixed(2)}`;
        document.getElementById('financeiro-contagem').textContent = count;
        document.getElementById('financeiro-media').textContent = `R$ ${media.toFixed(2)}`;
        document.getElementById('financeiro-recorrentes').textContent = recorrentes;
        
        document.getElementById('total-financeiro').textContent = `R$ ${total.toFixed(2)}`;
        
        if (doacoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">Nenhuma doação financeira</td></tr>';
            return;
        }
        
        tbody.innerHTML = doacoes.map(d => {
            const statusMap = {
                'confirmado': 'badge-success',
                'pendente': 'badge-warning',
                'cancelado': 'badge-danger'
            };
            const statusText = {
                'confirmado': '✅ Confirmado',
                'pendente': '⏳ Pendente',
                'cancelado': '❌ Cancelado'
            };
            return `
                <tr>
                    <td>${new Date(d.data_criacao).toLocaleDateString('pt-BR')}</td>
                    <td>${d.ong_nome || 'Desconhecida'}</td>
                    <td><strong>R$ ${d.valor.toFixed(2)}</strong></td>
                    <td><span class="badge badge-info">${d.metodo_pagamento}</span></td>
                    <td><span class="badge ${statusMap[d.status] || 'badge-warning'}">${statusText[d.status] || d.status}</span></td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #e74c3c;">Erro: ${error.message}</td></tr>`;
    }
}

// ==================== NOTIFICAÇÕES ====================
async function carregarPreferenciasNotificacoes() {
    try {
        const data = await apiRequest('/notificacoes/preferencias');
        document.getElementById('email-doacoes').checked = data.email_doacoes !== false;
        document.getElementById('email-novas-necessidades').checked = data.email_novas_necessidades !== false;
        document.getElementById('email-eventos').checked = data.email_eventos !== false;
        document.getElementById('email-newsletter').checked = data.email_newsletter === true;
        document.getElementById('push-doacoes').checked = data.push_doacoes !== false;
        document.getElementById('push-novas-necessidades').checked = data.push_novas_necessidades !== false;
        document.getElementById('push-eventos').checked = data.push_eventos !== false;
        document.getElementById('push-mensagens').checked = data.push_mensagens !== false;
    } catch (error) {
        console.error('Erro ao carregar preferências:', error);
    }
}

document.getElementById('form-notificacoes')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const preferencias = {
        email_doacoes: document.getElementById('email-doacoes').checked,
        email_novas_necessidades: document.getElementById('email-novas-necessidades').checked,
        email_eventos: document.getElementById('email-eventos').checked,
        email_newsletter: document.getElementById('email-newsletter').checked,
        push_doacoes: document.getElementById('push-doacoes').checked,
        push_novas_necessidades: document.getElementById('push-novas-necessidades').checked,
        push_eventos: document.getElementById('push-eventos').checked,
        push_mensagens: document.getElementById('push-mensagens').checked
    };
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const textoOriginal = submitBtn.textContent;
    submitBtn.textContent = 'Salvando...';
    submitBtn.disabled = true;
    
    try {
        await apiRequest('/notificacoes/preferencias', {
            method: 'PUT',
            body: JSON.stringify(preferencias)
        });
        showToast('Preferências salvas com sucesso!', 'success');
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.textContent = textoOriginal;
        submitBtn.disabled = false;
    }
});

// ==================== ALTERAR SENHA ====================
document.getElementById('form-alterar-senha')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const senhaAtual = document.getElementById('senha-atual').value;
    const novaSenha = document.getElementById('nova-senha').value;
    const confirmarSenha = document.getElementById('confirmar-senha').value;
    
    if (!senhaAtual || !novaSenha || !confirmarSenha) {
        showToast('Preencha todos os campos', 'error');
        return;
    }
    
    if (novaSenha !== confirmarSenha) {
        showToast('As senhas não coincidem', 'error');
        return;
    }
    
    const requisitos = validarSenhaForte(novaSenha);
    const validos = requisitos.filter(r => r.startsWith('✅')).length;
    if (validos < requisitos.length) {
        showToast('Senha não atende a todos os requisitos', 'error');
        return;
    }
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const textoOriginal = submitBtn.textContent;
    submitBtn.textContent = 'Alterando...';
    submitBtn.disabled = true;
    
    try {
        await apiRequest('/usuario/alterar-senha', {
            method: 'PUT',
            body: JSON.stringify({ senha_atual: senhaAtual, nova_senha: novaSenha })
        });
        showToast('Senha alterada com sucesso!', 'success');
        document.getElementById('form-alterar-senha').reset();
        document.getElementById('senha-forca').innerHTML = '';
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.textContent = textoOriginal;
        submitBtn.disabled = false;
    }
});

// ==================== ATUALIZAR PERFIL ====================
document.getElementById('form-perfil')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const dados = {
        nome: document.getElementById('nome').value,
        email: document.getElementById('email').value,
        telefone: document.getElementById('telefone').value,
        endereco: document.getElementById('endereco').value,
        cidade: document.getElementById('cidade').value,
        uf: document.getElementById('uf').value
    };
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const textoOriginal = submitBtn.textContent;
    submitBtn.textContent = 'Salvando...';
    submitBtn.disabled = true;
    
    try {
        await apiRequest('/usuario/atualizar', {
            method: 'PUT',
            body: JSON.stringify(dados)
        });
        showToast('Dados atualizados com sucesso!', 'success');
        await carregarPerfil();
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.textContent = textoOriginal;
        submitBtn.disabled = false;
    }
});

// ==================== 2FA ====================
let secret2FA = '';

async function carregarStatus2FA() {
    try {
        const data = await apiRequest('/usuario/2fa/status');
        const ativo = data.ativo || false;
        const container = document.getElementById('status-2fa');
        const btn = document.getElementById('btn-2fa');
        
        if (ativo) {
            container.innerHTML = '<p style="color: #27ae60;">✅ 2FA está ATIVO para sua conta</p>';
            btn.textContent = '🔓 Desativar 2FA';
            btn.onclick = desativar2FA;
        } else {
            container.innerHTML = '<p style="color: #7f8c8d;">❌ 2FA está DESATIVADO</p>';
            btn.textContent = '🔐 Ativar 2FA';
            btn.onclick = ativar2FA;
        }
    } catch (error) {
        console.error('Erro ao carregar status 2FA:', error);
    }
}

async function ativar2FA() {
    try {
        const data = await apiRequest('/usuario/2fa/ativar', { method: 'POST' });
        secret2FA = data.secret;
        document.getElementById('qr-code-img').src = `data:image/png;base64,${data.qr_code}`;
        document.getElementById('modal-2fa').style.display = 'flex';
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function confirmar2FA() {
    const codigo = document.getElementById('codigo-2fa').value;
    if (!codigo || codigo.length !== 6) {
        showToast('Digite o código de 6 dígitos', 'error');
        return;
    }
    try {
        await apiRequest('/usuario/2fa/confirmar', {
            method: 'POST',
            body: JSON.stringify({ codigo, secret: secret2FA })
        });
        showToast('2FA ativado com sucesso!', 'success');
        fecharModal('modal-2fa');
        carregarStatus2FA();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function desativar2FA() {
    if (!confirm('Tem certeza que deseja desativar o 2FA?')) return;
    try {
        await apiRequest('/usuario/2fa/desativar', { method: 'DELETE' });
        showToast('2FA desativado com sucesso', 'info');
        carregarStatus2FA();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ==================== RELATÓRIO ANUAL ====================
async function gerarRelatorioAnual() {
    const ano = document.getElementById('ano-relatorio').value;
    const container = document.getElementById('relatorio-conteudo');
    const modal = document.getElementById('modal-relatorio');
    const statusDiv = document.getElementById('relatorio-status');
    
    statusDiv.innerHTML = '<p style="color: #f39c12;">⏳ Gerando relatório...</p>';
    
    try {
        const data = await apiRequest('/relatorios/anual/gerar', {
            method: 'POST',
            body: JSON.stringify({ ano: parseInt(ano) })
        });
        
        container.innerHTML = `
            <div style="padding: 1rem;">
                <p><strong>✅ Relatório gerado com sucesso!</strong></p>
                <p><strong>Ano:</strong> ${data.ano}</p>
                <p><strong>Data:</strong> ${new Date().toLocaleString()}</p>
                <hr style="margin: 1rem 0;">
                <a href="${data.download_url}" class="btn btn-primary" style="width: 100%; text-align: center;" target="_blank">
                    📥 Baixar PDF
                </a>
                <button class="btn btn-outline" onclick="fecharModal('modal-relatorio')" style="width: 100%; margin-top: 0.5rem;">
                    Fechar
                </button>
            </div>
        `;
        
        modal.style.display = 'flex';
        statusDiv.innerHTML = '<p style="color: #27ae60;">✅ Relatório gerado com sucesso! Clique em "Baixar PDF" para fazer o download.</p>';
        
    } catch (error) {
        statusDiv.innerHTML = `<p style="color: #e74c3c;">❌ Erro: ${error.message}</p>`;
        showToast(error.message, 'error');
    }
}

// ==================== EXPORTAÇÃO DE DADOS ====================
async function solicitarExportacaoDados() {
    try {
        const data = await apiRequest('/usuario/exportar-dados', { method: 'POST' });
        const blob = new Blob([JSON.stringify(data.dados, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `meus_dados_${new Date().toISOString().slice(0,10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('Dados exportados com sucesso!', 'success');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ==================== EXCLUSÃO DE CONTA ====================
async function solicitarExclusaoConta() {
    if (!confirm('⚠️ Tem certeza que deseja EXCLUIR sua conta? Esta ação é irreversível!')) return;
    if (!confirm('🔴 Última confirmação: Deseja realmente excluir sua conta permanentemente?')) return;
    try {
        await apiRequest('/usuario/excluir', { method: 'DELETE' });
        showToast('Solicitação de exclusão recebida. Sua conta será removida em até 30 dias.', 'info');
        localStorage.clear();
        setTimeout(() => { window.location.href = '/'; }, 3000);
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ==================== TABS ====================
function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(`tab-${tabId}`).classList.add('active');
        });
    });
}

// ==================== MODAL ====================
function fecharModal(id) {
    document.getElementById(id).style.display = 'none';
}

// ==================== FORÇA DA SENHA EM TEMPO REAL ====================
document.addEventListener('DOMContentLoaded', function() {
    const novaSenha = document.getElementById('nova-senha');
    if (novaSenha) {
        novaSenha.addEventListener('input', function() {
            atualizarForcaSenha(this.value);
        });
    }
});

// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', async () => {
    await obterCsrfToken();
    setupAuth();
    setupTabs();
    await carregarPerfil();
});

// ==================== FUNÇÕES GLOBAIS ====================
window.solicitarExportacaoDados = solicitarExportacaoDados;
window.solicitarExclusaoConta = solicitarExclusaoConta;
window.ativar2FA = ativar2FA;
window.confirmar2FA = confirmar2FA;
window.gerarRelatorioAnual = gerarRelatorioAnual;
window.fecharModal = fecharModal;
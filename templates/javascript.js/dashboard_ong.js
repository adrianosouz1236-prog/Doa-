// dashboard_ong.js
const API_BASE_URL = window.location.origin + '/api';
let csrfToken = '';

async function obterCsrfToken() {
    try {
        const response = await fetch(`${API_BASE_URL}/config/csrf-token`);
        const data = await response.json();
        csrfToken = data.csrf_token || '';
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
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
        'X-CSRF-Token': csrfToken
    };
}

async function apiRequest(endpoint, options = {}) {
    try {
        const url = `${API_BASE_URL}${endpoint}`;
        console.log(`📡 ${options.method || 'GET'}: ${url}`);
        
        const response = await fetch(url, {
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
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getOngId() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    return user.id;
}

function scrollToSection(sectionId) {
    const targetId = sectionId.replace('#', '');
    const section = document.getElementById(targetId);
    if (section) {
        const navbarHeight = document.querySelector('.header')?.offsetHeight || 70;
        const sectionPosition = section.getBoundingClientRect().top + window.pageYOffset - navbarHeight - 20;
        
        window.scrollTo({
            top: sectionPosition,
            behavior: 'smooth'
        });
        
        if (history.pushState) {
            history.pushState(null, null, `#${targetId}`);
        }
    }
}

function setupScrollLinks() {
    document.querySelectorAll('.scroll-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('data-target') || this.getAttribute('href').replace('#', '');
            if (target) {
                scrollToSection(target);
            }
        });
    });
}

function mostrarSeguranca() {
    scrollToSection('seguranca-section');
    document.getElementById('seguranca-section').style.display = 'block';
}

document.getElementById('form-alterar-senha-ong')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const senhaAtual = document.getElementById('senha-atual-ong').value;
    const novaSenha = document.getElementById('nova-senha-ong').value;
    const confirmarSenha = document.getElementById('confirmar-senha-ong').value;
    
    if (!senhaAtual || !novaSenha || !confirmarSenha) {
        showToast('Preencha todos os campos', 'error');
        return;
    }
    
    if (novaSenha !== confirmarSenha) {
        showToast('As senhas não coincidem', 'error');
        return;
    }
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const textoOriginal = submitBtn.textContent;
    submitBtn.textContent = '⏳ Alterando...';
    submitBtn.disabled = true;
    
    try {
        await apiRequest('/usuario/alterar-senha', {
            method: 'PUT',
            body: JSON.stringify({ 
                senha_atual: senhaAtual, 
                nova_senha: novaSenha 
            })
        });
        
        showToast('✅ Senha alterada com sucesso!', 'success');
        document.getElementById('form-alterar-senha-ong').reset();
        
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.textContent = textoOriginal;
        submitBtn.disabled = false;
    }
});

async function solicitarExclusaoContaOng() {
    if (!confirm('⚠️ Tem certeza que deseja EXCLUIR sua conta? Esta ação é irreversível!')) return;
    if (!confirm('🔴 Última confirmação: Deseja realmente excluir sua conta permanentemente?')) return;
    
    const statusDiv = document.getElementById('status-exclusao-ong');
    statusDiv.innerHTML = '<p style="color: #f39c12;">⏳ Processando solicitação...</p>';
    
    try {
        const data = await apiRequest('/usuario/excluir', { method: 'DELETE' });
        
        statusDiv.innerHTML = `
            <p style="color: #27ae60;">✅ ${data.message}</p>
            <p style="color: #7f8c8d; font-size: 0.9rem;">Prazo: ${data.prazo}</p>
            <p style="color: #7f8c8d; font-size: 0.9rem;">ID da solicitação: ${data.solicitacao_id}</p>
        `;
        
        showToast('Solicitação de exclusão enviada com sucesso!', 'success');
        
        document.querySelector('.btn-danger[onclick="solicitarExclusaoContaOng()"]').disabled = true;
        document.querySelector('.btn-danger[onclick="solicitarExclusaoContaOng()"]').textContent = '✅ Solicitação Enviada';
        document.querySelector('.btn-danger[onclick="solicitarExclusaoContaOng()"]').style.opacity = '0.6';
        
    } catch (error) {
        statusDiv.innerHTML = `<p style="color: #e74c3c;">❌ Erro: ${error.message}</p>`;
        showToast(error.message, 'error');
    }
}

async function carregarDashboard() {
    try {
        const data = await apiRequest('/ongs/dashboard');
        document.getElementById('stat-necessidades').textContent = data.total_necessidades || 0;
        document.getElementById('stat-doacoes').textContent = data.total_doacoes || 0;
        document.getElementById('stat-itens').textContent = data.total_itens || 0;
        document.getElementById('stat-doadores').textContent = data.total_doadores || 0;
        document.getElementById('stat-eventos').textContent = data.total_eventos || 0;
        document.getElementById('stat-doacoes-financeiras').textContent = data.total_doacoes_financeiras || 0;
        document.getElementById('stat-saldo-carteira').textContent = `R$ ${(data.saldo_carteira || 0).toFixed(2)}`;
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
    }
}

async function carregarCarteira() {
    try {
        const data = await apiRequest('/carteira/saldo');
        document.getElementById('carteira-saldo').textContent = `R$ ${(data.saldo || 0).toFixed(2)}`;
        document.getElementById('carteira-recebido').textContent = `R$ ${(data.total_recebido || 0).toFixed(2)}`;
        document.getElementById('carteira-sacado').textContent = `R$ ${(data.total_sacado || 0).toFixed(2)}`;
        document.getElementById('stat-saldo-carteira').textContent = `R$ ${(data.saldo || 0).toFixed(2)}`;
        await carregarExtrato();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function carregarExtrato() {
    try {
        const data = await apiRequest('/carteira/extrato');
        const extrato = data.extrato || [];
        const tbody = document.getElementById('carteira-extrato-tbody');
        if (extrato.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">Nenhuma transação encontrada</td></tr>';
            return;
        }
        tbody.innerHTML = extrato.map(t => {
            const tipoIcon = t.tipo === 'entrada' ? '💰 Entrada' : '💸 Saída';
            const valorClass = t.tipo === 'entrada' ? 'text-success' : 'text-danger';
            const statusClass = t.status === 'confirmado' ? 'badge-success' : 'badge-warning';
            return `
                <tr>
                    <td>${new Date(t.data_criacao).toLocaleString()}</td>
                    <td><code>${t.transacao_id}</code></td>
                    <td>${tipoIcon}</td>
                    <td class="${valorClass}">${t.tipo === 'entrada' ? '+' : '-'} R$ ${t.valor.toFixed(2)}</td>
                    <td><span class="badge ${statusClass}">${t.status}</span></td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Erro ao carregar extrato:', error);
    }
}

function abrirModalSaque() {
    apiRequest('/carteira/saldo').then(data => {
        document.getElementById('saque-saldo-disponivel').textContent = `R$ ${(data.saldo || 0).toFixed(2)}`;
        document.getElementById('conta-saque').value = data.conta_bancaria || '';
    }).catch(error => { showToast(error.message, 'error'); });
    document.getElementById('valor-saque').value = '';
    document.getElementById('saque-modal').style.display = 'flex';
}

document.getElementById('form-saque')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const valor = parseFloat(document.getElementById('valor-saque').value);
    const contaBancaria = document.getElementById('conta-saque').value;
    if (!valor || valor < 10) {
        showToast('Valor mínimo para saque é R$ 10,00', 'error');
        return;
    }
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const textoOriginal = submitBtn.textContent;
    submitBtn.textContent = 'Processando...';
    submitBtn.disabled = true;
    try {
        await apiRequest('/carteira/sacar', {
            method: 'POST',
            body: JSON.stringify({ valor, conta_bancaria: contaBancaria })
        });
        showToast('Saque solicitado com sucesso!', 'success');
        fecharModal('saque-modal');
        carregarCarteira();
        carregarDashboard();
        carregarDoacoesFinanceirasOng();
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.textContent = textoOriginal;
        submitBtn.disabled = false;
    }
});

// ==================== NECESSIDADES ====================

async function carregarMinhasNecessidades() {
    try {
        const data = await apiRequest('/ongs/necessidades');
        const necessidades = data.necessidades || [];
        const tbody = document.getElementById('necessidades-tbody');
        if (necessidades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Nenhuma necessidade cadastrada</td></tr>';
            return;
        }
        tbody.innerHTML = necessidades.map(n => {
            const statusClass = n.status === 'aberta' ? 'badge-success' : 'badge-warning';
            return `
                <tr>
                    <td>${escapeHtml(n.titulo)}</td>
                    <td><span class="badge badge-info">${n.categoria}</span></td>
                    <td>${n.quantidade_necessaria}</td>
                    <td>${n.quantidade_recebida || 0}</td>
                    <td><span class="badge ${statusClass}">${n.status === 'aberta' ? 'Ativa' : 'Encerrada'}</span></td>
                    <td>
                        <button class="btn btn-outline btn-sm" onclick="editarNecessidade(${n.id})">✏️</button>
                        ${n.status === 'aberta' ? `<button class="btn btn-danger btn-sm" onclick="encerrarNecessidade(${n.id})">🔚</button>` : ''}
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function abrirModalNecessidade(necessidade = null) {
    document.getElementById('necessidade-id').value = necessidade?.id || '';
    document.getElementById('titulo').value = necessidade?.titulo || '';
    document.getElementById('categoria').value = necessidade?.categoria || 'alimentos';
    document.getElementById('descricao').value = necessidade?.descricao || '';
    document.getElementById('quantidade_necessaria').value = necessidade?.quantidade_necessaria || '';
    document.getElementById('urgencia').value = necessidade?.urgencia || 'media';
    document.getElementById('modal-title').textContent = necessidade ? 'Editar Necessidade' : 'Cadastrar Nova Necessidade';
    document.getElementById('necessidade-modal').style.display = 'flex';
}

async function editarNecessidade(id) {
    try {
        const data = await apiRequest(`/ongs/necessidades/${id}`);
        abrirModalNecessidade(data);
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function encerrarNecessidade(id) {
    if (!confirm('Tem certeza que deseja encerrar esta necessidade?')) return;
    try {
        await apiRequest(`/ongs/necessidades/${id}/encerrar`, { method: 'PUT' });
        showToast('Necessidade encerrada!', 'success');
        carregarMinhasNecessidades();
        carregarDashboard();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

document.getElementById('necessidade-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('necessidade-id').value;
    const dados = {
        titulo: document.getElementById('titulo').value,
        categoria: document.getElementById('categoria').value,
        descricao: document.getElementById('descricao').value,
        quantidade_necessaria: parseInt(document.getElementById('quantidade_necessaria').value),
        urgencia: document.getElementById('urgencia').value
    };
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const textoOriginal = submitBtn.textContent;
    submitBtn.textContent = 'Salvando...';
    submitBtn.disabled = true;
    try {
        if (id) {
            await apiRequest(`/ongs/necessidades/${id}`, { method: 'PUT', body: JSON.stringify(dados) });
            showToast('Necessidade atualizada!', 'success');
        } else {
            await apiRequest('/ongs/necessidades', { method: 'POST', body: JSON.stringify(dados) });
            showToast('Necessidade criada!', 'success');
        }
        fecharModal('necessidade-modal');
        carregarMinhasNecessidades();
        carregarDashboard();
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.textContent = textoOriginal;
        submitBtn.disabled = false;
    }
});

// ==================== DOAÇÕES RECEBIDAS ====================

async function carregarDoacoesRecebidas() {
    try {
        const data = await apiRequest('/ongs/doacoes');
        const doacoes = data.doacoes || [];
        const tbody = document.getElementById('doacoes-tbody');
        if (doacoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Nenhuma doação recebida</td></tr>';
            return;
        }
        tbody.innerHTML = doacoes.map(d => {
            const statusClass = d.status === 'confirmada' ? 'badge-success' : 'badge-warning';
            return `
                <tr>
                    <td>${new Date(d.data).toLocaleString()}</td>
                    <td>${escapeHtml(d.doador_nome || 'Anônimo')}</td>
                    <td>${escapeHtml(d.necessidade_titulo)}</td>
                    <td>${d.quantidade}</td>
                    <td><span class="badge ${statusClass}">${d.status || 'Pendente'}</span></td>
                    <td>${d.status !== 'confirmada' ? `<button class="btn btn-success btn-sm" onclick="confirmarDoacao(${d.id})">✅ Confirmar</button>` : '-'}</td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function confirmarDoacao(id) {
    if (!confirm('Confirmar esta doação?')) return;
    try {
        await apiRequest(`/ongs/doacoes/${id}/confirmar`, { method: 'PUT' });
        showToast('Doação confirmada!', 'success');
        carregarDoacoesRecebidas();
        carregarDashboard();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ==================== DOAÇÕES FINANCEIRAS ====================

async function carregarDoacoesFinanceirasOng() {
    try {
        const data = await apiRequest('/doacoes/financeiras/ong');
        const doacoes = data.doacoes || [];
        const tbody = document.getElementById('doacoes-financeiras-tbody');
        if (doacoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">Nenhuma doação financeira recebida</td></tr>';
            return;
        }
        tbody.innerHTML = doacoes.map(d => {
            const statusClass = d.status === 'confirmado' ? 'badge-success' : 'badge-warning';
            const statusText = d.status === 'confirmado' ? '✅ Confirmado' : '⏳ Pendente';
            return `
                <tr>
                    <td>${new Date(d.data_criacao).toLocaleString()}</td>
                    <td><strong>${escapeHtml(d.doador_nome)}</strong></td>
                    <td>R$ ${d.valor.toFixed(2)}</td>
                    <td>R$ ${(d.taxa_servico || 0).toFixed(2)}</td>
                    <td><strong>R$ ${(d.valor_liquido || 0).toFixed(2)}</strong></td>
                    <td><span class="badge badge-info">${d.metodo_pagamento}</span></td>
                    <td>${d.mensagem ? escapeHtml(d.mensagem.substring(0, 30)) + (d.mensagem.length > 30 ? '...' : '') : '-'}</td>
                    <td><span class="badge ${statusClass}">${statusText}</span></td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Erro ao carregar doações financeiras:', error);
    }
}

// ==================== EVENTOS ====================

async function carregarMeusEventos() {
    try {
        const data = await apiRequest('/ongs/eventos');
        const eventos = data.eventos || [];
        const tbody = document.getElementById('eventos-tbody');
        if (eventos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">Nenhum evento cadastrado</td></tr>';
            return;
        }
        tbody.innerHTML = eventos.map(e => {
            const statusClass = e.status === 'ativo' ? 'badge-success' : 'badge-warning';
            return `
                <tr>
                    <td>${escapeHtml(e.titulo)}</td>
                    <td>${new Date(e.data_evento).toLocaleString()}</td>
                    <td>${escapeHtml(e.local_evento || 'Não informado')}</td>
                    <td><span class="badge ${statusClass}">${e.status === 'ativo' ? 'Ativo' : 'Concluído'}</span></td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="cancelarEvento(${e.id})">❌ Cancelar</button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function abrirModalEvento() {
    document.getElementById('evento-id').value = '';
    document.getElementById('evento-titulo').value = '';
    document.getElementById('evento-descricao').value = '';
    document.getElementById('evento-data').value = '';
    document.getElementById('evento-local').value = '';
    document.getElementById('evento-endereco').value = '';
    document.getElementById('evento-cidade').value = '';
    document.getElementById('evento-uf').value = '';
    document.getElementById('evento-imagem').value = '';
    document.getElementById('evento-modal').style.display = 'flex';
}

async function cancelarEvento(id) {
    if (!confirm('Cancelar este evento?')) return;
    try {
        await apiRequest(`/ongs/eventos/${id}/cancelar`, { method: 'PUT' });
        showToast('Evento cancelado!', 'success');
        carregarMeusEventos();
        carregarDashboard();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

document.getElementById('evento-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const dados = {
        titulo: document.getElementById('evento-titulo').value,
        descricao: document.getElementById('evento-descricao').value,
        data_evento: document.getElementById('evento-data').value,
        local_evento: document.getElementById('evento-local').value,
        endereco: document.getElementById('evento-endereco').value,
        cidade: document.getElementById('evento-cidade').value,
        uf: document.getElementById('evento-uf').value,
        imagem_url: document.getElementById('evento-imagem').value
    };
    try {
        await apiRequest('/ongs/eventos', { method: 'POST', body: JSON.stringify(dados) });
        showToast('Evento criado!', 'success');
        fecharModal('evento-modal');
        carregarMeusEventos();
        carregarDashboard();
    } catch (error) {
        showToast(error.message, 'error');
    }
});

// ==================== PARCERIAS ====================

async function carregarMinhasParcerias() {
    try {
        const data = await apiRequest('/ongs/parcerias');
        const parcerias = data.parcerias || [];
        const tbody = document.getElementById('parcerias-tbody');
        if (parcerias.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">Nenhuma parceria cadastrada</td></tr>';
            return;
        }
        tbody.innerHTML = parcerias.map(p => {
            const statusClass = p.status === 'ativa' ? 'badge-success' : 'badge-warning';
            return `
                <tr>
                    <td><strong>${escapeHtml(p.parceiro_nome)}</strong></td>
                    <td><span class="badge badge-info">${p.tipo_parceria}</span></td>
                    <td>${escapeHtml(p.descricao?.substring(0, 50) || '-')}</td>
                    <td><span class="badge ${statusClass}">${p.status}</span></td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="encerrarParceria(${p.id})">🔚 Encerrar</button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function abrirModalParceria() {
    document.getElementById('parceria-id').value = '';
    document.getElementById('parceria-nome').value = '';
    document.getElementById('parceria-tipo').value = 'empresa';
    document.getElementById('parceria-descricao').value = '';
    document.getElementById('parceria-logo').value = '';
    document.getElementById('parceria-website').value = '';
    document.getElementById('parceria-modal').style.display = 'flex';
}

async function encerrarParceria(id) {
    if (!confirm('Encerrar esta parceria?')) return;
    try {
        await apiRequest(`/ongs/parcerias/${id}/encerrar`, { method: 'PUT' });
        showToast('Parceria encerrada!', 'success');
        carregarMinhasParcerias();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

document.getElementById('parceria-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const dados = {
        parceiro_nome: document.getElementById('parceria-nome').value,
        tipo_parceria: document.getElementById('parceria-tipo').value,
        descricao: document.getElementById('parceria-descricao').value,
        logo_url: document.getElementById('parceria-logo').value,
        website_url: document.getElementById('parceria-website').value
    };
    try {
        await apiRequest('/ongs/parcerias', { method: 'POST', body: JSON.stringify(dados) });
        showToast('Parceria adicionada!', 'success');
        fecharModal('parceria-modal');
        carregarMinhasParcerias();
    } catch (error) {
        showToast(error.message, 'error');
    }
});

// ==================== FOTOS ====================

async function carregarFotosOng() {
    try {
        const data = await apiRequest('/ongs/fotos');
        const fotos = data.fotos || [];
        const container = document.getElementById('fotos-lista');
        const modalContainer = document.getElementById('fotos-lista-modal');
        
        if (fotos.length === 0) {
            const msg = '<p style="color: #7f8c8d;">Nenhuma foto cadastrada</p>';
            if (container) container.innerHTML = msg;
            if (modalContainer) modalContainer.innerHTML = msg;
        } else {
            const html = `
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1rem;">
                    ${fotos.map(f => `
                        <div style="position: relative; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <img src="${f.foto_url}" alt="${escapeHtml(f.descricao || 'Foto')}" style="width: 100%; height: 150px; object-fit: cover;">
                            <p style="padding: 0.5rem; font-size: 0.8rem; text-align: center;">${escapeHtml(f.descricao || 'Sem descrição')}</p>
                            <button class="btn btn-danger btn-sm" style="position: absolute; top: 5px; right: 5px; padding: 0.2rem 0.5rem;" onclick="removerFoto(${f.id})">✕</button>
                        </div>
                    `).join('')}
                </div>
                <p style="color: #7f8c8d; margin-top: 0.5rem; font-size: 0.8rem;">${fotos.length}/3 fotos</p>
            `;
            if (container) container.innerHTML = html;
            if (modalContainer) modalContainer.innerHTML = html;
        }
        
        document.getElementById('foto-url').value = '';
        document.getElementById('foto-descricao').value = '';
        document.getElementById('fotos-modal').style.display = 'flex';
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function removerFoto(fotoId) {
    if (!confirm('Remover esta foto?')) return;
    try {
        await apiRequest(`/ongs/fotos/${fotoId}`, { method: 'DELETE' });
        showToast('Foto removida!', 'success');
        carregarFotosOng();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

document.getElementById('fotos-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const dados = {
        foto_url: document.getElementById('foto-url').value,
        descricao: document.getElementById('foto-descricao').value
    };
    try {
        await apiRequest('/ongs/fotos', { method: 'POST', body: JSON.stringify(dados) });
        showToast('Foto adicionada!', 'success');
        carregarFotosOng();
    } catch (error) {
        showToast(error.message, 'error');
    }
});

// ==================== LOCALIZAÇÃO ====================

function carregarLocalizacaoOng() {
    document.getElementById('localizacao-modal').style.display = 'flex';
}

function buscarLocalizacao() {
    const endereco = document.getElementById('loc-endereco').value;
    if (!endereco) {
        showToast('Digite um endereço para buscar', 'warning');
        return;
    }
    showToast('🔍 Buscando localização...', 'info');
    setTimeout(() => {
        document.getElementById('loc-latitude').value = '-23.550520';
        document.getElementById('loc-longitude').value = '-46.633308';
        showToast('📍 Localização encontrada!', 'success');
    }, 1000);
}

function obterLocalizacaoAtual() {
    if (navigator.geolocation) {
        showToast('📍 Obtendo localização...', 'info');
        navigator.geolocation.getCurrentPosition(
            (position) => {
                document.getElementById('loc-latitude').value = position.coords.latitude;
                document.getElementById('loc-longitude').value = position.coords.longitude;
                showToast('📍 Localização obtida com sucesso!', 'success');
            },
            (error) => {
                showToast('❌ Erro ao obter localização: ' + error.message, 'error');
            }
        );
    } else {
        showToast('❌ Geolocalização não suportada pelo navegador', 'error');
    }
}

document.getElementById('localizacao-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const dados = {
        endereco: document.getElementById('loc-endereco').value,
        latitude: parseFloat(document.getElementById('loc-latitude').value),
        longitude: parseFloat(document.getElementById('loc-longitude').value)
    };
    if (!dados.latitude || !dados.longitude) {
        showToast('Localização não definida. Busque ou informe manualmente.', 'warning');
        return;
    }
    try {
        await apiRequest('/ongs/localizacao', { method: 'PUT', body: JSON.stringify(dados) });
        showToast('📍 Localização salva com sucesso!', 'success');
        fecharModal('localizacao-modal');
        const mapaContainer = document.getElementById('mapa-container');
        if (mapaContainer) {
            mapaContainer.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                    <p style="color: #27ae60; font-size: 1.2rem;">✅ Localização salva!</p>
                    <p style="color: #7f8c8d;">Lat: ${dados.latitude}, Lng: ${dados.longitude}</p>
                    <p style="color: #7f8c8d;">Endereço: ${dados.endereco}</p>
                </div>
            `;
        }
        document.getElementById('ong-endereco-completo').textContent = dados.endereco;
    } catch (error) {
        showToast(error.message, 'error');
    }
});

// ==================== PERFIL ====================

async function carregarPerfilOng() {
    try {
        const data = await apiRequest('/ongs/perfil');
        document.getElementById('ong-nome').value = data.nome || '';
        document.getElementById('ong-email').value = data.email || '';
        document.getElementById('ong-telefone').value = data.telefone || '';
        document.getElementById('ong-endereco').value = data.endereco || '';
        document.getElementById('ong-cidade').value = data.cidade || '';
        document.getElementById('ong-uf').value = data.uf || '';
        document.getElementById('ong-descricao').value = data.descricao || '';
        document.getElementById('ong-logo').value = data.logo_url || '';
        document.getElementById('ong-conta-bancaria').value = data.conta_bancaria || '';
        document.getElementById('perfil-modal').style.display = 'flex';
    } catch (error) {
        showToast(error.message, 'error');
    }
}

document.getElementById('perfil-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const dados = {
        nome: document.getElementById('ong-nome').value,
        email: document.getElementById('ong-email').value,
        telefone: document.getElementById('ong-telefone').value,
        endereco: document.getElementById('ong-endereco').value,
        cidade: document.getElementById('ong-cidade').value,
        uf: document.getElementById('ong-uf').value,
        descricao: document.getElementById('ong-descricao').value,
        logo_url: document.getElementById('ong-logo').value,
        conta_bancaria: document.getElementById('ong-conta-bancaria').value
    };
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const textoOriginal = submitBtn.textContent;
    submitBtn.textContent = 'Salvando...';
    submitBtn.disabled = true;
    try {
        await apiRequest('/ongs/perfil', { method: 'PUT', body: JSON.stringify(dados) });
        showToast('Perfil atualizado!', 'success');
        fecharModal('perfil-modal');
        carregarDashboard();
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.textContent = textoOriginal;
        submitBtn.disabled = false;
    }
});

function abrirModal(id) { document.getElementById(id).style.display = 'flex'; }
function fecharModal(id) { document.getElementById(id).style.display = 'none'; }

// ==================== INICIALIZAÇÃO ====================

document.addEventListener('DOMContentLoaded', async () => {
    await obterCsrfToken();
    const token = getToken();
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (!token || !user.id) {
        window.location.href = '/login.html';
        return;
    }
    if (localStorage.getItem('userType') !== 'ong') {
        window.location.href = '/';
        return;
    }
    document.getElementById('user-name').textContent = user.nome?.split(' ')[0] || 'ONG';
    
    setupScrollLinks();
    
    if (window.location.hash) {
        setTimeout(() => {
            scrollToSection(window.location.hash);
        }, 500);
    }
    
    carregarDashboard();
    carregarMinhasNecessidades();
    carregarDoacoesRecebidas();
    carregarDoacoesFinanceirasOng();
    carregarCarteira();
    carregarMeusEventos();
    carregarMinhasParcerias();
    
    document.getElementById('logout-btn').addEventListener('click', () => {
        localStorage.clear();
        window.location.href = '/';
    });
});

window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.style.display = 'none';
    }
});

window.scrollToSection = scrollToSection;
window.abrirModalNecessidade = abrirModalNecessidade;
window.abrirModalEvento = abrirModalEvento;
window.abrirModalParceria = abrirModalParceria;
window.abrirModalSaque = abrirModalSaque;
window.carregarMinhasNecessidades = carregarMinhasNecessidades;
window.carregarMeusEventos = carregarMeusEventos;
window.carregarMinhasParcerias = carregarMinhasParcerias;
window.carregarDoacoesRecebidas = carregarDoacoesRecebidas;
window.carregarDoacoesFinanceirasOng = carregarDoacoesFinanceirasOng;
window.carregarCarteira = carregarCarteira;
window.carregarPerfilOng = carregarPerfilOng;
window.carregarFotosOng = carregarFotosOng;
window.carregarLocalizacaoOng = carregarLocalizacaoOng;
window.editarNecessidade = editarNecessidade;
window.encerrarNecessidade = encerrarNecessidade;
window.confirmarDoacao = confirmarDoacao;
window.removerFoto = removerFoto;
window.cancelarEvento = cancelarEvento;
window.encerrarParceria = encerrarParceria;
window.buscarLocalizacao = buscarLocalizacao;
window.obterLocalizacaoAtual = obterLocalizacaoAtual;
window.fecharModal = fecharModal;
window.getOngId = getOngId;
window.mostrarSeguranca = mostrarSeguranca;
window.solicitarExclusaoContaOng = solicitarExclusaoContaOng;
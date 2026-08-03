const API_BASE_URL = window.location.origin + '/api';
let ongsData = [], doadoresData = [], anunciosData = [], comunicacoesData = [];
let doacoesFinanceirasData = [], solicitacoesExclusaoData = [];
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

function showToast(msg, type) {
    const toast = document.getElementById('toast');
    toast.querySelector('.toast-message').textContent = msg;
    toast.className = `toast toast-${type}`;
    toast.style.display = 'block';
    setTimeout(() => toast.style.display = 'none', 3000);
}

function getToken() { return localStorage.getItem('token'); }

function getHeaders() {
    return { 
        'Content-Type': 'application/json', 
        'Authorization': `Bearer ${getToken()}`,
        'X-CSRF-Token': csrfToken
    };
}

async function requisicaoApi(endpoint, options = {}) {
    try {
        const res = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) { 
            if (res.status === 401) { localStorage.clear(); window.location.href = '/login.html'; } 
            throw new Error(data.error || 'Erro na requisição'); 
        }
        return data;
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
}

function mostrarAba(aba) {
    document.querySelectorAll('.tab-content').forEach(t => {
        t.style.display = 'none';
        t.classList.remove('active');
    });
    const abaElement = document.getElementById(`aba-${aba}`);
    if (abaElement) {
        abaElement.style.display = 'block';
        abaElement.classList.add('active');
    }
    document.querySelectorAll('.nav-link').forEach(l => {
        l.classList.remove('active');
        if (l.dataset.aba === aba) l.classList.add('active');
    });
    if (aba === 'dashboard') carregarDashboard();
    if (aba === 'anuncios') carregarAnuncios();
    if (aba === 'ongs') carregarOngs();
    if (aba === 'doadores') carregarDoadores();
    if (aba === 'doacoes') carregarDoacoes();
    if (aba === 'financeiro') { carregarDoacoesFinanceiras(); carregarCarteiras(); carregarCarteiraPlataforma(); }
    if (aba === 'feedback') carregarFeedbacksAdmin();
    if (aba === 'suporte') carregarSuportesAdmin();
    if (aba === 'comunicacao') carregarComunicacoesAdmin();
    if (aba === 'exclusoes') carregarSolicitacoesExclusao();
    if (aba === 'logs') carregarLogs();
}

function configurarEventosAbas() {
    document.querySelectorAll('.nav-link[data-aba]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const aba = this.dataset.aba;
            if (aba) mostrarAba(aba);
        });
    });
    document.querySelectorAll('.dropdown-menu a[data-aba]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const aba = this.dataset.aba;
            if (aba) mostrarAba(aba);
        });
    });
}

// ==================== DASHBOARD ====================

async function carregarDashboard() {
    try {
        const data = await requisicaoApi('/admin/dashboard');
        document.getElementById('total-ongs').textContent = data.total_ongs || 0;
        document.getElementById('total-doadores').textContent = data.total_doadores || 0;
        document.getElementById('total-anuncios').textContent = data.total_anuncios || 0;
        document.getElementById('total-advertencias').textContent = data.total_advertencias || 0;
        document.getElementById('total-doacoes').textContent = data.total_doacoes || 0;
        document.getElementById('total-doacoes-financeiras').textContent = data.total_doacoes_financeiras || 0;
        document.getElementById('total-valor-financeiro').textContent = `R$ ${(data.total_valor_financeiro || 0).toFixed(2)}`;
        document.getElementById('total-comunicacoes').textContent = data.total_comunicacoes || 0;
        document.getElementById('ongs-bloqueadas').textContent = data.ongs_bloqueadas || 0;
        document.getElementById('solicitacoes-exclusao').textContent = data.solicitacoes_exclusao_pendentes || 0;
        
        const logs = data.logs_recentes || [];
        document.getElementById('logs-recentes').innerHTML = logs.slice(0,10).map(l => 
            `<tr><td>${new Date(l.data).toLocaleString()}</td><td>${l.evento}</td><td>${l.usuario || '-'}</td><td>${l.ip || '-'}</td></tr>`
        ).join('');

        // Carregar carteira da plataforma
        await carregarCarteiraPlataforma();
    } catch(e) { showToast(e.message, 'error'); }
}

// ==================== CARTEIRA DA PLATAFORMA ====================

async function carregarCarteiraPlataforma() {
    try {
        const data = await requisicaoApi('/admin/carteira');
        const saldo = data.saldo || 0;
        const totalTaxas = data.total_taxas || 0;
        const totalSacado = data.total_sacado || 0;
        
        // Atualizar na dashboard
        const saldoEl = document.getElementById('plataforma-saldo');
        const taxasEl = document.getElementById('plataforma-total-taxas');
        const sacadoEl = document.getElementById('plataforma-total-sacado');
        if (saldoEl) saldoEl.textContent = `R$ ${saldo.toFixed(2)}`;
        if (taxasEl) taxasEl.textContent = `R$ ${totalTaxas.toFixed(2)}`;
        if (sacadoEl) sacadoEl.textContent = `R$ ${totalSacado.toFixed(2)}`;

        // Atualizar na aba financeiro
        const saldoFin = document.getElementById('plataforma-saldo-financeiro');
        const taxasFin = document.getElementById('plataforma-total-taxas-financeiro');
        const sacadoFin = document.getElementById('plataforma-total-sacado-financeiro');
        if (saldoFin) saldoFin.textContent = `R$ ${saldo.toFixed(2)}`;
        if (taxasFin) taxasFin.textContent = `R$ ${totalTaxas.toFixed(2)}`;
        if (sacadoFin) sacadoFin.textContent = `R$ ${totalSacado.toFixed(2)}`;

        // Atualizar saldo no modal
        const saldoModal = document.getElementById('saque-plataforma-saldo');
        if (saldoModal) saldoModal.textContent = `R$ ${saldo.toFixed(2)}`;

    } catch (error) {
        console.error('Erro ao carregar carteira da plataforma:', error);
    }
}

function abrirModalSaquePlataforma() {
    // Remover modal existente se houver
    const modalExistente = document.getElementById('modal-saque-plataforma');
    if (modalExistente) {
        modalExistente.style.display = 'flex';
        carregarCarteiraPlataforma();
        return;
    }

    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'modal-saque-plataforma';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>💸 Saque da Carteira da Plataforma</h3>
                <span class="modal-close" onclick="fecharModal('modal-saque-plataforma')">&times;</span>
            </div>
            <form id="form-saque-plataforma">
                <div class="form-group">
                    <label>Valor (R$) *</label>
                    <input type="number" id="valor-saque-plataforma" min="10" step="0.01" required placeholder="Mínimo R$ 10,00">
                    <small style="color: #7f8c8d;">Saldo disponível: <span id="saque-plataforma-saldo">R$ 0,00</span></small>
                </div>
                <div class="form-group">
                    <label>Conta Bancária *</label>
                    <input type="text" id="conta-saque-plataforma" required placeholder="Banco - Agência - Conta">
                </div>
                <button type="submit" class="btn btn-primary" style="width: 100%;">💸 Solicitar Saque</button>
            </form>
        </div>
    `;
    document.body.appendChild(modal);

    // Carregar saldo atual
    carregarCarteiraPlataforma();

    // Configurar submit do formulário
    document.getElementById('form-saque-plataforma').addEventListener('submit', async (e) => {
        e.preventDefault();
        const valor = parseFloat(document.getElementById('valor-saque-plataforma').value);
        const contaBancaria = document.getElementById('conta-saque-plataforma').value;

        if (!valor || valor < 10) {
            showToast('Valor mínimo para saque é R$ 10,00', 'error');
            return;
        }

        if (!contaBancaria) {
            showToast('Informe a conta bancária', 'error');
            return;
        }

        const submitBtn = e.target.querySelector('button[type="submit"]');
        const textoOriginal = submitBtn.textContent;
        submitBtn.textContent = 'Processando...';
        submitBtn.disabled = true;

        try {
            const data = await requisicaoApi('/admin/carteira/sacar', {
                method: 'POST',
                body: JSON.stringify({ valor, conta_bancaria: contaBancaria })
            });
            showToast(`Saque de R$ ${valor.toFixed(2)} realizado com sucesso!`, 'success');
            fecharModal('modal-saque-plataforma');
            carregarCarteiraPlataforma();
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            submitBtn.textContent = textoOriginal;
            submitBtn.disabled = false;
        }
    });
}

// ==================== ANÚNCIOS ====================

async function carregarAnuncios() {
    try {
        const data = await requisicaoApi('/admin/anuncios');
        anunciosData = data.anuncios || [];
        renderizarAnuncios(anunciosData);
    } catch(e) { showToast(e.message, 'error'); }
}

function renderizarAnuncios(anuncios) {
    document.getElementById('anuncios-tbody').innerHTML = anuncios.map(a => {
        let statusBadge = '', statusText = '';
        if (a.excluido) { statusBadge = 'badge-inactive'; statusText = 'Excluído'; }
        else if (a.total_advertencias > 0) { statusBadge = 'badge-warning'; statusText = `⚠️ ${a.total_advertencias} advertência(s)`; }
        else { statusBadge = 'badge-active'; statusText = 'Ativo'; }
        return `
            <tr>
                <td>${a.id}</td><td>${escapeHtml(a.ong_nome)}</td><td>${escapeHtml(a.titulo)}</td>
                <td><span class="badge badge-info">${a.categoria}</span></td>
                <td>${a.urgencia === 'alta' ? '<span class="text-danger">🔴 Alta</span>' : a.urgencia === 'media' ? '<span class="text-warning">🟡 Média</span>' : '🟢 Baixa'}</td>
                <td><span class="badge ${statusBadge}">${statusText}</span></td>
                <td>${a.total_advertencias || 0}</td>
                <td>${new Date(a.data_criacao).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="verAnuncio(${a.id})">👁️</button>
                    <button class="btn btn-warning btn-sm" onclick="abrirModalAdvertenciaParaId(${a.id}, ${a.ong_id})">⚠️</button>
                    ${!a.excluido ? `<button class="btn btn-danger btn-sm" onclick="excluirAnuncioPorId(${a.id})">🗑️</button>` : ''}
                </td>
            </tr>
        `;
    }).join('');
}

function filtrarAnuncios() {
    const termo = document.getElementById('buscar-anuncio').value.toLowerCase();
    const filtroStatus = document.getElementById('filtro-status-anuncio').value;
    let filtrados = anunciosData;
    if (termo) filtrados = filtrados.filter(a => a.titulo.toLowerCase().includes(termo) || a.ong_nome.toLowerCase().includes(termo));
    if (filtroStatus === 'normal') filtrados = filtrados.filter(a => !a.excluido && a.total_advertencias === 0);
    else if (filtroStatus === 'advertencia') filtrados = filtrados.filter(a => !a.excluido && a.total_advertencias > 0);
    else if (filtroStatus === 'excluido') filtrados = filtrados.filter(a => a.excluido);
    renderizarAnuncios(filtrados);
}

let anuncioAtualId = null, ongAtualId = null;

async function verAnuncio(id) {
    const anuncio = anunciosData.find(a => a.id == id);
    if (anuncio) {
        anuncioAtualId = anuncio.id; ongAtualId = anuncio.ong_id;
        document.getElementById('anuncio-detalhes').innerHTML = `
            <p><strong>ONG:</strong> ${escapeHtml(anuncio.ong_nome)}</p>
            <p><strong>Título:</strong> ${escapeHtml(anuncio.titulo)}</p>
            <p><strong>Categoria:</strong> ${anuncio.categoria}</p>
            <p><strong>Descrição:</strong> ${escapeHtml(anuncio.descricao)}</p>
            <p><strong>Quantidade:</strong> ${anuncio.quantidade_necessaria} itens</p>
            <p><strong>Recebidos:</strong> ${anuncio.quantidade_recebida || 0} itens</p>
            <p><strong>Urgência:</strong> ${anuncio.urgencia}</p>
            <p><strong>Status:</strong> ${anuncio.excluido ? 'Excluído' : (anuncio.total_advertencias > 0 ? `${anuncio.total_advertencias} advertência(s)` : 'Ativo')}</p>
        `;
        if (anuncio.advertencias && anuncio.advertencias.length > 0) {
            document.getElementById('anuncio-advertencias').innerHTML = `
                <div class="advertencia-list"><strong>📋 Histórico de Advertências:</strong><br>
                ${anuncio.advertencias.map(adv => `<div class="advertencia-item"><strong>${new Date(adv.data).toLocaleDateString()}</strong> - ${adv.motivo}<br><small>${adv.descricao}</small></div>`).join('')}</div>
            `;
        } else {
            document.getElementById('anuncio-advertencias').innerHTML = '<p class="text-muted">Nenhuma advertência registrada.</p>';
        }
        abrirModal('modal-anuncio');
    }
}

function abrirModalAdvertenciaParaId(anuncioId, ongId) {
    anuncioAtualId = anuncioId; ongAtualId = ongId;
    abrirModalAdvertencia();
}

function abrirModalAdvertencia() {
    document.getElementById('form-advertencia').reset();
    document.getElementById('advertencia-anuncio-id').value = anuncioAtualId;
    document.getElementById('advertencia-ong-id').value = ongAtualId;
    abrirModal('modal-advertencia');
}

async function excluirAnuncio() {
    if (!confirm('⚠️ Tem certeza que deseja EXCLUIR este anúncio?')) return;
    await excluirAnuncioPorId(anuncioAtualId);
}

async function excluirAnuncioPorId(id) {
    try {
        await requisicaoApi(`/admin/anuncios/${id}/excluir`, { method: 'DELETE' });
        showToast('Anúncio excluído com sucesso!', 'success');
        fecharModal('modal-anuncio');
        fecharModal('modal-advertencia');
        carregarAnuncios();
        carregarDashboard();
    } catch(e) { showToast(e.message, 'error'); }
}

// ==================== ONGs ====================

async function carregarOngs() {
    try { 
        const data = await requisicaoApi('/admin/ongs'); 
        ongsData = data.ongs || []; 
        renderizarOngs(ongsData);
    } catch(e) { showToast(e.message, 'error'); }
}

function renderizarOngs(ongs) {
    document.getElementById('ongs-tbody').innerHTML = ongs.map(o => {
        const estrelas = '★'.repeat(Math.round(o.media_avaliacao || 0)) + '☆'.repeat(5 - Math.round(o.media_avaliacao || 0));
        return `
            <tr>
                <td>${o.id}</td><td>${escapeHtml(o.nome)}</td><td>${o.cnpj || '-'}</td>
                <td>${o.email}</td><td>${o.cidade || '-'}</td>
                <td><span class="badge ${o.status === 'ativo' ? 'badge-active' : 'badge-inactive'}">${o.status}</span></td>
                <td>${o.total_advertencias || 0}</td>
                <td>${estrelas} (${o.media_avaliacao || 0})</td>
                <td>R$ ${(o.saldo_carteira || 0).toFixed(2)}</td>
                <td>${new Date(o.data_cadastro).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="verOng(${o.id})">👁️</button>
                    ${o.status !== 'bloqueado' ? `<button class="btn btn-danger btn-sm" onclick="bloquearOngPorId(${o.id})">🔒</button>` : ''}
                </td>
            </tr>
        `;
    }).join('');
}

function filtrarOngs() {
    const termo = document.getElementById('buscar-ong').value.toLowerCase();
    renderizarOngs(ongsData.filter(o => o.nome.toLowerCase().includes(termo) || o.email.toLowerCase().includes(termo)));
}

async function verOng(id) {
    const ong = ongsData.find(o => o.id == id);
    if (ong) {
        const estrelas = '★'.repeat(Math.round(ong.media_avaliacao || 0)) + '☆'.repeat(5 - Math.round(ong.media_avaliacao || 0));
        document.getElementById('ong-detalhes').innerHTML = `
            <p><strong>Nome:</strong> ${escapeHtml(ong.nome)}</p>
            <p><strong>CNPJ:</strong> ${ong.cnpj || '-'}</p>
            <p><strong>Email:</strong> ${ong.email}</p>
            <p><strong>Telefone:</strong> ${ong.telefone || '-'}</p>
            <p><strong>Endereço:</strong> ${ong.endereco || '-'}</p>
            <p><strong>Cidade:</strong> ${ong.cidade || '-'}</p>
            <p><strong>⭐ Avaliação:</strong> ${estrelas} (${ong.media_avaliacao || 0} de 5)</p>
            <p><strong>💰 Saldo:</strong> R$ ${(ong.saldo_carteira || 0).toFixed(2)}</p>
            <p><strong>Status:</strong> <span class="badge ${ong.status === 'ativo' ? 'badge-active' : 'badge-inactive'}">${ong.status}</span></p>
            <p><strong>Total de Advertências:</strong> ${ong.total_advertencias || 0}</p>
        `;
        if (ong.advertencias && ong.advertencias.length > 0) {
            document.getElementById('ong-advertencias').innerHTML = `
                <div class="advertencia-list"><strong>📋 Histórico de Advertências:</strong><br>
                ${ong.advertencias.map(adv => `<div class="advertencia-item"><strong>${new Date(adv.data).toLocaleDateString()}</strong> - Anúncio #${adv.anuncio_id}<br><strong>Motivo:</strong> ${adv.motivo}<br><small>${adv.descricao}</small></div>`).join('')}</div>
            `;
        } else {
            document.getElementById('ong-advertencias').innerHTML = '<p>Nenhuma advertência registrada.</p>';
        }
        const btnBloquear = document.getElementById('btn-bloquear-ong');
        if (ong.status === 'bloqueado') {
            btnBloquear.textContent = '🔓 Desbloquear ONG';
            btnBloquear.onclick = () => desbloquearOng(ong.id);
            btnBloquear.classList.remove('btn-danger');
            btnBloquear.classList.add('btn-primary');
        } else {
            btnBloquear.textContent = '🔒 Bloquear ONG';
            btnBloquear.onclick = () => bloquearOngPorId(ong.id);
            btnBloquear.classList.remove('btn-primary');
            btnBloquear.classList.add('btn-danger');
        }
        abrirModal('modal-ong');
    }
}

async function bloquearOngPorId(id) {
    if (!confirm('⚠️ Tem certeza que deseja BLOQUEAR esta ONG?')) return;
    try {
        await requisicaoApi(`/admin/ongs/${id}/bloquear`, { method: 'PUT' });
        showToast('ONG bloqueada com sucesso!', 'warning');
        carregarOngs();
        carregarDashboard();
        fecharModal('modal-ong');
    } catch(e) { showToast(e.message, 'error'); }
}

async function desbloquearOng(id) {
    try {
        await requisicaoApi(`/admin/ongs/${id}/desbloquear`, { method: 'PUT' });
        showToast('ONG desbloqueada com sucesso!', 'success');
        carregarOngs();
        carregarDashboard();
        fecharModal('modal-ong');
    } catch(e) { showToast(e.message, 'error'); }
}

function bloquearOng() {
    const ongId = document.querySelector('#ong-detalhes')?.dataset?.ongId;
    if (ongId) bloquearOngPorId(parseInt(ongId));
}

// ==================== DOADORES ====================

async function carregarDoadores() {
    try { 
        const data = await requisicaoApi('/admin/doadores'); 
        doadoresData = data.doadores || []; 
        renderizarDoadores(doadoresData);
    } catch(e) { showToast(e.message, 'error'); }
}

function renderizarDoadores(doadores) {
    document.getElementById('doadores-tbody').innerHTML = doadores.map(d => {
        const conquistas = d.conquistas || [];
        const iconesConquistas = conquistas.map(c => {
            const icones = { 'primeira_doacao': '🌟', 'doador_frequente': '⭐', 'doador_master': '🏆', '100_pontos': '💎', '500_pontos': '👑', '1000_pontos': '🔥' };
            return icones[c] || '🎯';
        }).join(' ');
        return `
            <tr>
                <td>${d.id}</td><td>${escapeHtml(d.nome)}</td><td>${d.email}</td>
                <td>${d.telefone || '-'}</td><td>${d.total_doacoes || 0}</td>
                <td>${d.pontuacao || 0}</td><td>${iconesConquistas || '-'}</td>
                <td><span class="badge ${d.status === 'ativo' ? 'badge-active' : 'badge-inactive'}">${d.status}</span></td>
                <td>${new Date(d.data_cadastro).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="verDoador(${d.id})">👁️</button>
                    ${d.status !== 'bloqueado' ? `<button class="btn btn-danger btn-sm" onclick="bloquearDoadorPorId(${d.id})">🔒</button>` : ''}
                </td>
            </tr>
        `;
    }).join('');
}

function filtrarDoadores() {
    const termo = document.getElementById('buscar-doador').value.toLowerCase();
    renderizarDoadores(doadoresData.filter(d => d.nome.toLowerCase().includes(termo) || d.email.toLowerCase().includes(termo)));
}

function exportarDoadores() {
    const csv = doadoresData.map(d => `${d.id},${d.nome},${d.email},${d.total_doacoes},${d.pontuacao},${d.status}`).join('\n');
    baixarCSV(csv, 'doadores.csv');
}

async function verDoador(id) {
    const doador = doadoresData.find(d => d.id == id);
    if (doador) {
        const conquistas = doador.conquistas || [];
        const iconesConquistas = conquistas.map(c => {
            const icones = { 'primeira_doacao': '🌟 Primeira Doação', 'doador_frequente': '⭐ Doador Frequente', 'doador_master': '🏆 Doador Master', '100_pontos': '💎 100 Pontos', '500_pontos': '👑 500 Pontos', '1000_pontos': '🔥 1000 Pontos' };
            return icones[c] || c;
        }).join('\n');
        alert(`📋 DOADOR\n\nNome: ${doador.nome}\nEmail: ${doador.email}\nTelefone: ${doador.telefone}\nTotal doações: ${doador.total_doacoes}\nPontuação: ${doador.pontuacao}\nConquistas: ${iconesConquistas || 'Nenhuma'}\nStatus: ${doador.status}`);
    }
}

async function bloquearDoadorPorId(id) {
    if (!confirm('Bloquear este doador?')) return;
    try {
        await requisicaoApi(`/admin/doadores/${id}/bloquear`, { method: 'PUT' });
        showToast('Doador bloqueado!', 'warning');
        carregarDoadores();
    } catch(e) { showToast(e.message, 'error'); }
}

// ==================== DOAÇÕES ====================

async function carregarDoacoes() {
    try { 
        const data = await requisicaoApi('/admin/doacoes'); 
        document.getElementById('doacoes-tbody').innerHTML = (data.doacoes || []).map(d => 
            `<tr><td>${new Date(d.data).toLocaleString()}</td><td>${escapeHtml(d.doador_nome)}</td><td>${escapeHtml(d.ong_nome)}</td><td>${escapeHtml(d.item)}</td><td>${d.quantidade}</td><td><span class="badge ${d.status === 'confirmada' ? 'badge-active' : 'badge-pending'}">${d.status}</span></td></tr>`
        ).join('');
    } catch(e) { showToast(e.message, 'error'); }
}

// ==================== DOAÇÕES FINANCEIRAS ====================

async function carregarDoacoesFinanceiras() {
    try {
        const data = await requisicaoApi('/admin/doacoes/financeiras');
        doacoesFinanceirasData = data.doacoes || [];
        const total = doacoesFinanceirasData.length;
        const valorTotal = doacoesFinanceirasData.reduce((sum, d) => sum + (d.status === 'confirmado' ? d.valor : 0), 0);
        const valorMedio = total > 0 ? valorTotal / total : 0;
        const recorrentes = doacoesFinanceirasData.filter(d => d.recorrente).length;
        document.getElementById('financeiro-total').textContent = total;
        document.getElementById('financeiro-valor-total').textContent = `R$ ${valorTotal.toFixed(2)}`;
        document.getElementById('financeiro-valor-medio').textContent = `R$ ${valorMedio.toFixed(2)}`;
        document.getElementById('financeiro-recorrentes').textContent = recorrentes;
        renderizarDoacoesFinanceiras(doacoesFinanceirasData);
    } catch(e) { showToast(e.message, 'error'); }
}

function renderizarDoacoesFinanceiras(doacoes) {
    const filtro = document.getElementById('filtro-status-financeiro').value;
    let filtradas = doacoes;
    if (filtro !== 'todos') filtradas = filtradas.filter(d => d.status === filtro);
    document.getElementById('financeiro-tbody').innerHTML = filtradas.map(d => {
        const statusMap = { 'confirmado': 'badge-active', 'pendente': 'badge-pending', 'cancelado': 'badge-inactive' };
        const statusText = { 'confirmado': '✅ Confirmado', 'pendente': '⏳ Pendente', 'cancelado': '❌ Cancelado' };
        return `
            <tr>
                <td>${d.id}</td><td><code>${d.transacao_id}</code></td>
                <td>${escapeHtml(d.doador_nome)}</td><td>${escapeHtml(d.ong_nome)}</td>
                <td><strong>R$ ${d.valor.toFixed(2)}</strong></td>
                <td>R$ ${(d.taxa_servico || 0).toFixed(2)}</td>
                <td>R$ ${(d.valor_liquido || d.valor || 0).toFixed(2)}</td>
                <td><span class="badge badge-info">${d.metodo_pagamento}</span></td>
                <td>${d.recorrente ? '🔄 Sim' : '❌ Não'}</td>
                <td><span class="badge ${statusMap[d.status] || 'badge-pending'}">${statusText[d.status] || d.status}</span></td>
                <td>${new Date(d.data_criacao).toLocaleString()}</td>
            </tr>
        `;
    }).join('');
}

async function gerarRelatorioFinanceiro() {
    try {
        const data = await requisicaoApi('/admin/relatorios/gerar', {
            method: 'POST',
            body: JSON.stringify({ tipo: 'financeiro' })
        });
        const relatorio = data.dados || {};
        document.getElementById('relatorio-financeiro-conteudo').innerHTML = `
            <div style="padding: 1rem;">
                <h4>📊 Relatório Financeiro</h4>
                <p><strong>Gerado em:</strong> ${new Date(relatorio.data_geracao).toLocaleString()}</p>
                <hr>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div class="stat-card"><h3>Total Doações</h3><div class="stat-value">${relatorio.total_doacoes_financeiras || 0}</div></div>
                    <div class="stat-card"><h3>💰 Valor Total</h3><div class="stat-value">R$ ${(relatorio.valor_total || 0).toFixed(2)}</div></div>
                    <div class="stat-card"><h3>📊 Valor Médio</h3><div class="stat-value">R$ ${(relatorio.valor_medio || 0).toFixed(2)}</div></div>
                    <div class="stat-card"><h3>💰 Taxas Arrecadadas</h3><div class="stat-value">R$ ${(relatorio.total_taxas || 0).toFixed(2)}</div></div>
                </div>
                <button class="btn btn-primary" onclick="fecharModal('modal-relatorio-financeiro')" style="margin-top: 1rem;">Fechar</button>
            </div>
        `;
        abrirModal('modal-relatorio-financeiro');
    } catch(e) { showToast(e.message, 'error'); }
}

async function carregarCarteiras() {
    try {
        const data = await requisicaoApi('/admin/ongs');
        const ongs = data.ongs || [];
        document.getElementById('carteiras-tbody').innerHTML = ongs
            .filter(o => (o.saldo_carteira || 0) > 0)
            .map(o => `
                <tr>
                    <td>${escapeHtml(o.nome)}</td>
                    <td><strong>R$ ${(o.saldo_carteira || 0).toFixed(2)}</strong></td>
                    <td>R$ ${(o.total_recebido || 0).toFixed(2)}</td>
                    <td>R$ ${(o.total_sacado || 0).toFixed(2)}</td>
                    <td>${new Date(o.data_atualizacao).toLocaleString()}</td>
                </tr>
            `).join('') || '<tr><td colspan="5" style="text-align: center;">Nenhuma ONG com saldo</td></tr>';
    } catch(e) { showToast(e.message, 'error'); }
}

// ==================== COMUNICAÇÃO ====================

function abrirModalComunicacao() {
    document.getElementById('form-comunicacao').reset();
    document.getElementById('destinatario-especifico').style.display = 'none';
    abrirModal('modal-comunicacao');
}

function toggleDestinatarioEspecifico() {
    const tipo = document.getElementById('comunicacao-tipo').value;
    document.getElementById('destinatario-especifico').style.display = tipo === 'especifico' ? 'block' : 'none';
}

async function carregarComunicacoesAdmin() {
    try {
        const data = await requisicaoApi('/admin/comunicacoes');
        comunicacoesData = data.comunicacoes || [];
        const total = comunicacoesData.length;
        const lidas = comunicacoesData.filter(c => c.lida).length;
        const naoLidas = total - lidas;
        document.getElementById('total-enviadas').textContent = total;
        document.getElementById('total-lidas').textContent = lidas;
        document.getElementById('total-nao-lidas').textContent = naoLidas;
        renderizarComunicacoes(comunicacoesData);
    } catch(e) { showToast(e.message, 'error'); }
}

function renderizarComunicacoes(comunicacoes) {
    const tbody = document.getElementById('comunicacoes-tbody');
    if (comunicacoes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">Nenhuma comunicação enviada</td></tr>';
        return;
    }
    tbody.innerHTML = comunicacoes.map(c => {
        const prioridadeLabels = { 'normal': '<span class="badge badge-active">Normal</span>', 'alta': '<span class="badge badge-warning">🟡 Alta</span>', 'urgente': '<span class="badge badge-inactive">🔴 Urgente</span>' };
        const tipoLabels = { 'todos': 'Todos', 'doadores': 'Doadores', 'ongs': 'ONGs', 'especifico': 'Específico' };
        let destinatario = tipoLabels[c.tipo] || c.tipo;
        if (c.tipo === 'especifico' && c.destinatario_nome) destinatario += `: ${c.destinatario_nome} (ID: ${c.destinatario_id})`;
        const statusLido = c.lida ? '✅ Lida' : '⏳ Não lida';
        const statusClass = c.lida ? 'badge-active' : 'badge-pending';
        return `
            <tr>
                <td>${new Date(c.data_envio).toLocaleString()}</td>
                <td><strong>${escapeHtml(c.titulo)}</strong></td>
                <td><span class="badge badge-info">${tipoLabels[c.tipo] || c.tipo}</span></td>
                <td>${escapeHtml(destinatario)}</td>
                <td>${prioridadeLabels[c.prioridade] || c.prioridade}</td>
                <td><span class="badge ${statusClass}">${statusLido}</span></td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="verComunicacao(${c.id})">👁️</button>
                    <button class="btn btn-danger btn-sm" onclick="deletarComunicacao(${c.id})">🗑️</button>
                </td>
            </tr>
        `;
    }).join('');
}

async function verComunicacao(id) {
    const comunicacao = comunicacoesData.find(c => c.id == id);
    if (comunicacao) {
        const prioridadeColors = { 'normal': '#27ae60', 'alta': '#f39c12', 'urgente': '#e74c3c' };
        const tipoLabels = { 'todos': 'Todos (Doadores + ONGs)', 'doadores': 'Apenas Doadores', 'ongs': 'Apenas ONGs', 'especifico': 'Usuário Específico' };
        let destinatario = tipoLabels[comunicacao.tipo] || comunicacao.tipo;
        if (comunicacao.tipo === 'especifico' && comunicacao.destinatario_nome) destinatario += `: ${comunicacao.destinatario_nome} (ID: ${comunicacao.destinatario_id})`;
        document.getElementById('comunicacao-detalhes').innerHTML = `
            <div style="border-left: 4px solid ${prioridadeColors[comunicacao.prioridade] || '#27ae60'}; padding-left: 1rem;">
                <p><strong>📌 Título:</strong> ${escapeHtml(comunicacao.titulo)}</p>
                <p><strong>📨 Enviado por:</strong> ${comunicacao.admin_email}</p>
                <p><strong>📅 Data:</strong> ${new Date(comunicacao.data_envio).toLocaleString()}</p>
                <p><strong>👥 Destinatários:</strong> ${escapeHtml(destinatario)}</p>
                <p><strong>⚡ Prioridade:</strong> <span style="color: ${prioridadeColors[comunicacao.prioridade] || '#27ae60'}; font-weight: bold;">${comunicacao.prioridade.toUpperCase()}</span></p>
                <p><strong>📊 Status:</strong> ${comunicacao.lida ? '✅ Lida' : '⏳ Não lida'}</p>
                ${comunicacao.data_leitura ? `<p><strong>📖 Data de leitura:</strong> ${new Date(comunicacao.data_leitura).toLocaleString()}</p>` : ''}
                <hr style="margin: 1rem 0;">
                <p><strong>📝 Mensagem:</strong></p>
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 5px; white-space: pre-wrap;">${escapeHtml(comunicacao.mensagem)}</div>
            </div>
        `;
        abrirModal('modal-ver-comunicacao');
    }
}

async function deletarComunicacao(id) {
    if (!confirm('⚠️ Tem certeza que deseja deletar esta comunicação?')) return;
    try {
        await requisicaoApi(`/admin/comunicacoes/${id}`, { method: 'DELETE' });
        showToast('Comunicação deletada com sucesso!', 'success');
        carregarComunicacoesAdmin();
        carregarDashboard();
    } catch(e) { showToast(e.message, 'error'); }
}

// ==================== FEEDBACK ====================

async function carregarFeedbacksAdmin() {
    try {
        const status = document.getElementById('filtro-status-feedback').value;
        const url = status !== 'todos' ? `/admin/feedback?status=${status}` : '/admin/feedback';
        const data = await requisicaoApi(url);
        const feedbacks = data.feedbacks || [];
        document.getElementById('feedback-admin-tbody').innerHTML = feedbacks.map(fb => `
            <tr>
                <td>${new Date(fb.data).toLocaleString()}</td>
                <td>${escapeHtml(fb.user_nome)}<br><small>${fb.user_email}</small></td>
                <td><span class="badge badge-info">${fb.tipo}</span></td>
                <td>${escapeHtml(fb.mensagem.substring(0, 80))}${fb.mensagem.length > 80 ? '...' : ''}</td>
                <td><span class="badge ${fb.status === 'respondido' ? 'badge-active' : 'badge-pending'}">${fb.status}</span></td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="verFeedback(${fb.id})">👁️</button>
                    ${fb.status !== 'respondido' ? `<button class="btn btn-primary btn-sm" onclick="abrirResponderFeedback(${fb.id})">✉️</button>` : ''}
                </td>
            </tr>
        `).join('');
    } catch(e) { showToast(e.message, 'error'); }
}

async function verFeedback(id) {
    try {
        const data = await requisicaoApi('/admin/feedback');
        const feedback = data.feedbacks?.find(f => f.id == id);
        if (feedback) {
            document.getElementById('feedback-detalhes').innerHTML = `
                <p><strong>Usuário:</strong> ${escapeHtml(feedback.user_nome)}</p>
                <p><strong>Email:</strong> ${feedback.user_email}</p>
                <p><strong>Tipo:</strong> ${feedback.tipo}</p>
                <p><strong>Data:</strong> ${new Date(feedback.data).toLocaleString()}</p>
                <p><strong>Mensagem:</strong></p>
                <p style="background: #f8f9fa; padding: 0.8rem; border-radius: 5px;">${escapeHtml(feedback.mensagem)}</p>
                ${feedback.resposta ? `<p><strong>Resposta:</strong></p><p style="background: #e8f5e9; padding: 0.8rem; border-radius: 5px;">${escapeHtml(feedback.resposta)}</p>` : ''}
            `;
            document.getElementById('feedback-id').value = feedback.id;
            document.getElementById('feedback-resposta').value = '';
            abrirModal('modal-responder-feedback');
        }
    } catch(e) { showToast(e.message, 'error'); }
}

function abrirResponderFeedback(id) {
    document.getElementById('feedback-id').value = id;
    document.getElementById('feedback-resposta').value = '';
    document.getElementById('feedback-detalhes').innerHTML = '<p>Carregando...</p>';
    verFeedback(id);
}

// ==================== SUPORTE ====================

async function carregarSuportesAdmin() {
    try {
        const status = document.getElementById('filtro-status-suporte').value;
        const url = status !== 'todos' ? `/admin/suporte?status=${status}` : '/admin/suporte';
        const data = await requisicaoApi(url);
        const suportes = data.suportes || [];
        document.getElementById('suporte-admin-tbody').innerHTML = suportes.map(sp => {
            const statusMap = { 'aberto': 'badge-pending', 'em_andamento': 'badge-warning', 'resolvido': 'badge-active', 'fechado': 'badge-inactive' };
            const statusClass = statusMap[sp.status] || 'badge-pending';
            return `
                <tr>
                    <td>${new Date(sp.data).toLocaleString()}</td>
                    <td>${escapeHtml(sp.user_nome)}<br><small>${sp.user_email}</small></td>
                    <td><span class="badge badge-info">${sp.categoria}</span></td>
                    <td>${escapeHtml(sp.assunto)}</td>
                    <td><span class="badge ${statusClass}">${sp.status}</span></td>
                    <td>
                        <button class="btn btn-outline btn-sm" onclick="verSuporte(${sp.id})">👁️</button>
                        ${sp.status !== 'fechado' ? `<button class="btn btn-primary btn-sm" onclick="abrirResponderSuporte(${sp.id})">✉️</button>` : ''}
                    </td>
                </tr>
            `;
        }).join('');
    } catch(e) { showToast(e.message, 'error'); }
}

async function verSuporte(id) {
    try {
        const data = await requisicaoApi('/admin/suporte');
        const suporte = data.suportes?.find(s => s.id == id);
        if (suporte) {
            document.getElementById('suporte-detalhes').innerHTML = `
                <p><strong>Usuário:</strong> ${escapeHtml(suporte.user_nome)}</p>
                <p><strong>Email:</strong> ${suporte.user_email}</p>
                <p><strong>Categoria:</strong> ${suporte.categoria}</p>
                <p><strong>Status:</strong> ${suporte.status}</p>
                <p><strong>Data:</strong> ${new Date(suporte.data).toLocaleString()}</p>
                <p><strong>Assunto:</strong></p>
                <p style="background: #f8f9fa; padding: 0.8rem; border-radius: 5px;">${escapeHtml(suporte.assunto)}</p>
                <p><strong>Mensagem:</strong></p>
                <p style="background: #f8f9fa; padding: 0.8rem; border-radius: 5px;">${escapeHtml(suporte.mensagem)}</p>
                ${suporte.resposta ? `<p><strong>Resposta:</strong></p><p style="background: #e8f5e9; padding: 0.8rem; border-radius: 5px;">${escapeHtml(suporte.resposta)}</p>` : ''}
            `;
            document.getElementById('suporte-id').value = suporte.id;
            document.getElementById('suporte-resposta').value = '';
            document.getElementById('suporte-status').value = suporte.status || 'em_andamento';
            abrirModal('modal-responder-suporte');
        }
    } catch(e) { showToast(e.message, 'error'); }
}

function abrirResponderSuporte(id) {
    document.getElementById('suporte-id').value = id;
    document.getElementById('suporte-resposta').value = '';
    document.getElementById('suporte-status').value = 'em_andamento';
    document.getElementById('suporte-detalhes').innerHTML = '<p>Carregando...</p>';
    verSuporte(id);
}

// ==================== LOGS ====================

async function carregarLogs() {
    try { 
        const data = await requisicaoApi('/admin/logs'); 
        document.getElementById('logs-tbody').innerHTML = (data.logs || []).map(l => 
            `<tr><td>${new Date(l.data).toLocaleString()}</td><td>${l.evento}</td><td>${l.usuario || '-'}</td><td>${l.ip || '-'}</td><td><span class="badge ${l.gravidade === 'alta' ? 'badge-inactive' : 'badge-active'}">${l.gravidade}</span></td></tr>`
        ).join('');
    } catch(e) { showToast(e.message, 'error'); }
}

// ==================== EXCLUSÕES ====================

async function carregarSolicitacoesExclusao() {
    try {
        const data = await requisicaoApi('/admin/solicitacoes/exclusao');
        solicitacoesExclusaoData = data.solicitacoes || [];
        renderizarSolicitacoesExclusao(solicitacoesExclusaoData);
    } catch(e) { showToast(e.message, 'error'); }
}

function renderizarSolicitacoesExclusao(solicitacoes) {
    const tbody = document.getElementById('solicitacoes-exclusao-tbody');
    if (solicitacoes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Nenhuma solicitação de exclusão pendente</td></tr>';
        return;
    }
    tbody.innerHTML = solicitacoes.map(s => {
        const diasRestantes = calcularDiasRestantes(s.data_solicitacao);
        return `
            <tr>
                <td>${new Date(s.data_solicitacao).toLocaleString()}</td>
                <td><strong>${escapeHtml(s.usuario_nome)}</strong></td>
                <td>${s.usuario_email}</td>
                <td><span class="badge badge-info">${s.usuario_tipo}</span></td>
                <td>
                    <span class="badge ${diasRestantes > 0 ? 'badge-warning' : 'badge-danger'}">
                        ${diasRestantes > 0 ? `⏳ ${diasRestantes} dias` : '🔴 Excluir agora'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="confirmarExclusaoAdmin(${s.id})">
                        🗑️ Excluir Agora
                    </button>
                    <button class="btn btn-outline btn-sm" onclick="cancelarExclusao(${s.id})">
                        ❌ Cancelar
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function calcularDiasRestantes(dataSolicitacao) {
    const data = new Date(dataSolicitacao);
    const agora = new Date();
    const diff = 30 - Math.floor((agora - data) / (1000 * 60 * 60 * 24));
    return Math.max(0, diff);
}

function filtrarExclusoes() {
    const termo = document.getElementById('buscar-exclusao').value.toLowerCase();
    const filtrados = solicitacoesExclusaoData.filter(s => 
        s.usuario_nome.toLowerCase().includes(termo) || 
        s.usuario_email.toLowerCase().includes(termo)
    );
    renderizarSolicitacoesExclusao(filtrados);
}

async function confirmarExclusaoAdmin(solicitacaoId) {
    if (!confirm('⚠️ Tem certeza que deseja EXCLUIR esta conta imediatamente?')) return;
    if (!confirm('🔴 Esta ação é IRREVERSÍVEL! Todos os dados serão perdidos.')) return;
    
    try {
        await requisicaoApi(`/admin/solicitacoes/exclusao/${solicitacaoId}/confirmar`, {
            method: 'DELETE'
        });
        showToast('Conta excluída com sucesso!', 'success');
        carregarSolicitacoesExclusao();
        carregarDashboard();
    } catch(e) { showToast(e.message, 'error'); }
}

async function cancelarExclusao(solicitacaoId) {
    if (!confirm('Deseja cancelar a solicitação de exclusão?')) return;
    
    try {
        await requisicaoApi(`/admin/solicitacoes/exclusao/${solicitacaoId}/cancelar`, {
            method: 'PUT'
        });
        showToast('Solicitação cancelada com sucesso!', 'info');
        carregarSolicitacoesExclusao();
    } catch(e) { showToast(e.message, 'error'); }
}

// ==================== UTILITÁRIOS ====================

function exportarOngs() { 
    const csv = ongsData.map(o => `${o.id},${o.nome},${o.email},${o.status},${o.media_avaliacao},${o.saldo_carteira}`).join('\n'); 
    baixarCSV(csv, 'ongs.csv'); 
}

function exportarLogs() { showToast('Exportação em desenvolvimento', 'info'); }

function baixarCSV(conteudo, arquivo) { 
    const blob = new Blob([conteudo], { type: 'text/csv' }); 
    const a = document.createElement('a'); 
    a.href = URL.createObjectURL(blob); 
    a.download = arquivo; 
    a.click(); 
    URL.revokeObjectURL(a.href); 
}

function escapeHtml(texto) { 
    if(!texto) return ''; 
    const div = document.createElement('div'); 
    div.textContent = texto; 
    return div.innerHTML; 
}

function abrirModal(id) { document.getElementById(id).style.display = 'flex'; }
function fecharModal(id) { document.getElementById(id).style.display = 'none'; }

// ==================== INICIALIZAÇÃO ====================

document.addEventListener('DOMContentLoaded', async function() {
    await obterCsrfToken();
    const token = getToken();
    if (!token) { window.location.href = '/login.html'; return; }
    const userType = localStorage.getItem('userType');
    if (userType !== 'admin') { window.location.href = '/'; return; }
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const adminName = document.getElementById('admin-name');
    if (adminName && user.nome) adminName.textContent = user.nome || 'Admin';
    
    configurarEventosAbas();
    mostrarAba('dashboard');
    
    document.getElementById('logout-btn').addEventListener('click', function(e) {
        e.preventDefault();
        localStorage.clear();
        window.location.href = '/';
    });
    
    // Form Advertência
    document.getElementById('form-advertencia').addEventListener('submit', async function(e) {
        e.preventDefault();
        const dados = {
            anuncio_id: document.getElementById('advertencia-anuncio-id').value,
            ong_id: document.getElementById('advertencia-ong-id').value,
            motivo: document.getElementById('motivo-advertencia').value,
            descricao: document.getElementById('descricao-advertencia').value,
            acao: document.getElementById('acao-advertencia').value
        };
        try {
            const resultado = await requisicaoApi('/admin/advertencias', { method: 'POST', body: JSON.stringify(dados) });
            showToast(resultado.message || 'Advertência aplicada com sucesso!', 'warning');
            fecharModal('modal-advertencia');
            fecharModal('modal-anuncio');
            carregarAnuncios();
            carregarOngs();
            carregarDashboard();
        } catch(e) { showToast(e.message, 'error'); }
    });
    
    // Form Comunicação
    document.getElementById('form-comunicacao').addEventListener('submit', async function(e) {
        e.preventDefault();
        const tipo = document.getElementById('comunicacao-tipo').value;
        const titulo = document.getElementById('comunicacao-titulo').value;
        const mensagem = document.getElementById('comunicacao-mensagem').value;
        const prioridade = document.getElementById('comunicacao-prioridade').value;
        const destinatarioId = document.getElementById('comunicacao-destinatario-id').value;
        const destinatarioTipo = document.getElementById('comunicacao-destinatario-tipo').value;
        
        if (!titulo || titulo.length < 3) { showToast('Título deve ter pelo menos 3 caracteres', 'error'); return; }
        if (!mensagem || mensagem.length < 5) { showToast('Mensagem deve ter pelo menos 5 caracteres', 'error'); return; }
        if (tipo === 'especifico' && !destinatarioId) { showToast('Para envio específico, informe o ID do usuário', 'error'); return; }
        
        const dados = { tipo, titulo, mensagem, prioridade };
        if (tipo === 'especifico') { dados.destinatario_id = parseInt(destinatarioId); dados.destinatario_tipo = destinatarioTipo; }
        
        const submitBtn = e.target.querySelector('button[type="submit"]');
        const textoOriginal = submitBtn.textContent;
        submitBtn.textContent = 'Enviando...';
        submitBtn.disabled = true;
        try {
            const resultado = await requisicaoApi('/admin/comunicacao/enviar', {
                method: 'POST',
                body: JSON.stringify(dados)
            });
            showToast(resultado.message || 'Comunicação enviada com sucesso!', 'success');
            fecharModal('modal-comunicacao');
            carregarComunicacoesAdmin();
            carregarDashboard();
        } catch(e) { showToast(e.message, 'error'); } finally {
            submitBtn.textContent = textoOriginal;
            submitBtn.disabled = false;
        }
    });
    
    // Form Configurações
    document.getElementById('form-config')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        showToast('Configurações salvas!', 'success');
    });
    
    // Form Responder Feedback
    document.getElementById('form-responder-feedback')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const id = document.getElementById('feedback-id').value;
        const resposta = document.getElementById('feedback-resposta').value;
        if (!resposta || resposta.length < 3) { showToast('Resposta deve ter pelo menos 3 caracteres', 'error'); return; }
        try {
            await requisicaoApi(`/admin/feedback/${id}`, { method: 'PUT', body: JSON.stringify({ resposta, status: 'respondido' }) });
            showToast('Feedback respondido com sucesso!', 'success');
            fecharModal('modal-responder-feedback');
            carregarFeedbacksAdmin();
            carregarDashboard();
        } catch(e) { showToast(e.message, 'error'); }
    });
    
    // Form Responder Suporte
    document.getElementById('form-responder-suporte')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const id = document.getElementById('suporte-id').value;
        const resposta = document.getElementById('suporte-resposta').value;
        const status = document.getElementById('suporte-status').value;
        if (!resposta || resposta.length < 3) { showToast('Resposta deve ter pelo menos 3 caracteres', 'error'); return; }
        try {
            await requisicaoApi(`/admin/suporte/${id}`, { method: 'PUT', body: JSON.stringify({ resposta, status }) });
            showToast('Solicitação de suporte respondida com sucesso!', 'success');
            fecharModal('modal-responder-suporte');
            carregarSuportesAdmin();
            carregarDashboard();
        } catch(e) { showToast(e.message, 'error'); }
    });
});

// Tornar funções globais
window.mostrarAba = mostrarAba;
window.carregarDashboard = carregarDashboard;
window.carregarAnuncios = carregarAnuncios;
window.carregarOngs = carregarOngs;
window.carregarDoadores = carregarDoadores;
window.carregarDoacoes = carregarDoacoes;
window.carregarDoacoesFinanceiras = carregarDoacoesFinanceiras;
window.carregarCarteiras = carregarCarteiras;
window.carregarCarteiraPlataforma = carregarCarteiraPlataforma;
window.carregarFeedbacksAdmin = carregarFeedbacksAdmin;
window.carregarSuportesAdmin = carregarSuportesAdmin;
window.carregarComunicacoesAdmin = carregarComunicacoesAdmin;
window.carregarSolicitacoesExclusao = carregarSolicitacoesExclusao;
window.carregarLogs = carregarLogs;
window.gerarRelatorioFinanceiro = gerarRelatorioFinanceiro;
window.abrirModalComunicacao = abrirModalComunicacao;
window.abrirModalAdvertencia = abrirModalAdvertencia;
window.abrirModalSaquePlataforma = abrirModalSaquePlataforma;
window.abrirModalAdvertenciaParaId = abrirModalAdvertenciaParaId;
window.verAnuncio = verAnuncio;
window.verOng = verOng;
window.verDoador = verDoador;
window.verFeedback = verFeedback;
window.verSuporte = verSuporte;
window.verComunicacao = verComunicacao;
window.bloquearOngPorId = bloquearOngPorId;
window.desbloquearOng = desbloquearOng;
window.bloquearOng = bloquearOng;
window.bloquearDoadorPorId = bloquearDoadorPorId;
window.excluirAnuncioPorId = excluirAnuncioPorId;
window.excluirAnuncio = excluirAnuncio;
window.deletarComunicacao = deletarComunicacao;
window.confirmarExclusaoAdmin = confirmarExclusaoAdmin;
window.cancelarExclusao = cancelarExclusao;
window.filtrarAnuncios = filtrarAnuncios;
window.filtrarOngs = filtrarOngs;
window.filtrarDoadores = filtrarDoadores;
window.filtrarExclusoes = filtrarExclusoes;
window.exportarOngs = exportarOngs;
window.exportarDoadores = exportarDoadores;
window.exportarLogs = exportarLogs;
window.abrirResponderFeedback = abrirResponderFeedback;
window.abrirResponderSuporte = abrirResponderSuporte;
window.toggleDestinatarioEspecifico = toggleDestinatarioEspecifico;
window.fecharModal = fecharModal;
window.abrirModal = abrirModal;
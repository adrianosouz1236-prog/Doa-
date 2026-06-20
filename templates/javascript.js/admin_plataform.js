const API_BASE_URL = window.location.origin + '/api';
let ongsData = [], doadoresData = [], anunciosData = [];

function showToast(msg, type) {
    const toast = document.getElementById('toast');
    toast.querySelector('.toast-message').textContent = msg;
    toast.className = `toast toast-${type}`;
    toast.style.display = 'block';
    setTimeout(() => toast.style.display = 'none', 3000);
}

function getToken() { return localStorage.getItem('token'); }
function getHeaders() { return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` }; }

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

// ==================== FUNÇÃO MOSTRAR ABA ====================
function mostrarAba(aba) {
    console.log('📑 Mostrando aba:', aba);
    
    // Esconder todas as abas
    document.querySelectorAll('.tab-content').forEach(t => {
        t.style.display = 'none';
        t.classList.remove('active');
    });
    
    // Mostrar a aba selecionada
    const abaElement = document.getElementById(`aba-${aba}`);
    if (abaElement) {
        abaElement.style.display = 'block';
        abaElement.classList.add('active');
        console.log('✅ Aba exibida:', aba);
    } else {
        console.warn('⚠️ Aba não encontrada:', aba);
    }
    
    // Remover classe active de todos os links
    document.querySelectorAll('.nav-link').forEach(l => {
        l.classList.remove('active');
    });
    
    // Adicionar classe active ao link correspondente
    document.querySelectorAll('.nav-link').forEach(l => {
        if (l.dataset.aba === aba) {
            l.classList.add('active');
        }
    });
    
    // Carregar dados da aba
    if (aba === 'dashboard') carregarDashboard();
    if (aba === 'anuncios') carregarAnuncios();
    if (aba === 'ongs') carregarOngs();
    if (aba === 'doadores') carregarDoadores();
    if (aba === 'doacoes') carregarDoacoes();
    if (aba === 'feedback') carregarFeedbacksAdmin();
    if (aba === 'suporte') carregarSuportesAdmin();
    if (aba === 'logs') carregarLogs();
}

// ==================== CONFIGURAR EVENTOS DAS ABAS ====================
function configurarEventosAbas() {
    // Usar event listener nos links do menu
    document.querySelectorAll('.nav-link[data-aba]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const aba = this.dataset.aba;
            if (aba) {
                mostrarAba(aba);
            }
        });
    });
    
    // Links do dropdown
    document.querySelectorAll('.dropdown-menu a[data-aba]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const aba = this.dataset.aba;
            if (aba) {
                mostrarAba(aba);
            }
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
        document.getElementById('total-feedback').textContent = data.total_feedback || 0;
        document.getElementById('total-suporte').textContent = data.total_suporte || 0;
        document.getElementById('ongs-bloqueadas').textContent = data.ongs_bloqueadas || 0;
        
        const logs = data.logs_recentes || [];
        document.getElementById('logs-recentes').innerHTML = logs.slice(0,10).map(l => 
            `<tr>
                <td>${new Date(l.data).toLocaleString()}</td>
                <td>${l.evento}</td>
                <td>${l.usuario || '-'}</td>
                <td>${l.ip || '-'}</td>
            </tr>`
        ).join('');
    } catch(e) { showToast(e.message, 'error'); }
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
        let statusBadge = '';
        let statusText = '';
        
        if (a.excluido) {
            statusBadge = 'badge-inactive';
            statusText = 'Excluído';
        } else if (a.total_advertencias > 0) {
            statusBadge = 'badge-warning';
            statusText = `⚠️ ${a.total_advertencias} advertência(s)`;
        } else {
            statusBadge = 'badge-active';
            statusText = 'Ativo';
        }
        
        return `
            <tr>
                <td>${a.id}</td>
                <td>${escapeHtml(a.ong_nome)}</td>
                <td>${escapeHtml(a.titulo)}</td>
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
    
    if (termo) {
        filtrados = filtrados.filter(a => a.titulo.toLowerCase().includes(termo) || a.ong_nome.toLowerCase().includes(termo));
    }
    
    if (filtroStatus === 'normal') {
        filtrados = filtrados.filter(a => !a.excluido && a.total_advertencias === 0);
    } else if (filtroStatus === 'advertencia') {
        filtrados = filtrados.filter(a => !a.excluido && a.total_advertencias > 0);
    } else if (filtroStatus === 'excluido') {
        filtrados = filtrados.filter(a => a.excluido);
    }
    
    renderizarAnuncios(filtrados);
}

let anuncioAtualId = null;
let ongAtualId = null;

async function verAnuncio(id) {
    const anuncio = anunciosData.find(a => a.id == id);
    if (anuncio) {
        anuncioAtualId = anuncio.id;
        ongAtualId = anuncio.ong_id;
        
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
                <div class="advertencia-list">
                    <strong>📋 Histórico de Advertências:</strong><br>
                    ${anuncio.advertencias.map(adv => `
                        <div class="advertencia-item">
                            <strong>${new Date(adv.data).toLocaleDateString()}</strong> - ${adv.motivo}<br>
                            <small>${adv.descricao}</small>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            document.getElementById('anuncio-advertencias').innerHTML = '<p class="text-muted">Nenhuma advertência registrada.</p>';
        }
        
        abrirModal('modal-anuncio');
    }
}

function abrirModalAdvertenciaParaId(anuncioId, ongId) {
    anuncioAtualId = anuncioId;
    ongAtualId = ongId;
    abrirModalAdvertencia();
}

function abrirModalAdvertencia() {
    document.getElementById('form-advertencia').reset();
    document.getElementById('advertencia-anuncio-id').value = anuncioAtualId;
    document.getElementById('advertencia-ong-id').value = ongAtualId;
    abrirModal('modal-advertencia');
}

async function excluirAnuncio() {
    if (!confirm('⚠️ Tem certeza que deseja EXCLUIR este anúncio? Esta ação não pode ser desfeita!')) return;
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
    document.getElementById('ongs-tbody').innerHTML = ongs.map(o => `
        <tr>
            <td>${o.id}</td>
            <td>${escapeHtml(o.nome)}</td>
            <td>${o.cnpj || '-'}</td>
            <td>${o.email}</td>
            <td>${o.cidade || '-'}</td>
            <td><span class="badge ${o.status === 'ativo' ? 'badge-active' : 'badge-inactive'}">${o.status}</span></td>
            <td>${o.total_advertencias || 0}</td>
            <td>${new Date(o.data_cadastro).toLocaleDateString()}</td>
            <td>
                <button class="btn btn-outline btn-sm" onclick="verOng(${o.id})">👁️</button>
                ${o.status !== 'bloqueado' ? `<button class="btn btn-danger btn-sm" onclick="bloquearOngPorId(${o.id})">🔒</button>` : ''}
            </td>
        </tr>
    `).join('');
}

function filtrarOngs() {
    const termo = document.getElementById('buscar-ong').value.toLowerCase();
    renderizarOngs(ongsData.filter(o => o.nome.toLowerCase().includes(termo) || o.email.toLowerCase().includes(termo)));
}

async function verOng(id) {
    const ong = ongsData.find(o => o.id == id);
    if (ong) {
        document.getElementById('ong-detalhes').innerHTML = `
            <p><strong>Nome:</strong> ${escapeHtml(ong.nome)}</p>
            <p><strong>CNPJ:</strong> ${ong.cnpj || '-'}</p>
            <p><strong>Email:</strong> ${ong.email}</p>
            <p><strong>Telefone:</strong> ${ong.telefone || '-'}</p>
            <p><strong>Endereço:</strong> ${ong.endereco || '-'}</p>
            <p><strong>Cidade:</strong> ${ong.cidade || '-'}</p>
            <p><strong>Status:</strong> <span class="badge ${ong.status === 'ativo' ? 'badge-active' : 'badge-inactive'}">${ong.status}</span></p>
            <p><strong>Total de Advertências:</strong> ${ong.total_advertencias || 0}</p>
        `;
        
        if (ong.advertencias && ong.advertencias.length > 0) {
            document.getElementById('ong-advertencias').innerHTML = `
                <div class="advertencia-list">
                    <strong>📋 Histórico de Advertências:</strong><br>
                    ${ong.advertencias.map(adv => `
                        <div class="advertencia-item">
                            <strong>${new Date(adv.data).toLocaleDateString()}</strong> - Anúncio #${adv.anuncio_id}<br>
                            <strong>Motivo:</strong> ${adv.motivo}<br>
                            <small>${adv.descricao}</small>
                        </div>
                    `).join('')}
                </div>
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
    if (!confirm('⚠️ Tem certeza que deseja BLOQUEAR esta ONG? Ela não poderá mais publicar anúncios!')) return;
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
    // Pega o ID da ONG do modal
    const ongId = document.querySelector('#ong-detalhes')?.dataset?.ongId;
    if (ongId) {
        bloquearOngPorId(parseInt(ongId));
    }
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
    document.getElementById('doadores-tbody').innerHTML = doadores.map(d => `
        <tr>
            <td>${d.id}</td>
            <td>${escapeHtml(d.nome)}</td>
            <td>${d.email}</td>
            <td>${d.telefone || '-'}</td>
            <td>${d.total_doacoes || 0}</td>
            <td><span class="badge ${d.status === 'ativo' ? 'badge-active' : 'badge-inactive'}">${d.status}</span></td>
            <td>${new Date(d.data_cadastro).toLocaleDateString()}</td>
            <td>
                <button class="btn btn-outline btn-sm" onclick="verDoador(${d.id})">👁️</button>
                ${d.status !== 'bloqueado' ? `<button class="btn btn-danger btn-sm" onclick="bloquearDoadorPorId(${d.id})">🔒</button>` : ''}
            </td>
        </tr>
    `).join('');
}

function filtrarDoadores() {
    const termo = document.getElementById('buscar-doador').value.toLowerCase();
    renderizarDoadores(doadoresData.filter(d => d.nome.toLowerCase().includes(termo) || d.email.toLowerCase().includes(termo)));
}

async function verDoador(id) {
    const doador = doadoresData.find(d => d.id == id);
    if (doador) {
        alert(`📋 DOADOR\nNome: ${doador.nome}\nEmail: ${doador.email}\nTelefone: ${doador.telefone}\nTotal doações: ${doador.total_doacoes}\nStatus: ${doador.status}`);
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
            `<tr>
                <td>${new Date(d.data).toLocaleString()}</td>
                <td>${escapeHtml(d.doador_nome)}</td>
                <td>${escapeHtml(d.ong_nome)}</td>
                <td>${escapeHtml(d.item)}</td>
                <td>${d.quantidade}</td>
                <td><span class="badge ${d.status === 'confirmada' ? 'badge-active' : 'badge-pending'}">${d.status}</span></td>
            </tr>`
        ).join('');
    } catch(e) { showToast(e.message, 'error'); }
}

// ==================== FEEDBACK ADMIN ====================
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
                ${feedback.resposta ? `
                    <p><strong>Resposta:</strong></p>
                    <p style="background: #e8f5e9; padding: 0.8rem; border-radius: 5px;">${escapeHtml(feedback.resposta)}</p>
                ` : ''}
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

// ==================== SUPORTE ADMIN ====================
async function carregarSuportesAdmin() {
    try {
        const status = document.getElementById('filtro-status-suporte').value;
        const url = status !== 'todos' ? `/admin/suporte?status=${status}` : '/admin/suporte';
        const data = await requisicaoApi(url);
        const suportes = data.suportes || [];
        
        document.getElementById('suporte-admin-tbody').innerHTML = suportes.map(sp => {
            const statusMap = {
                'aberto': 'badge-pending',
                'em_andamento': 'badge-warning',
                'resolvido': 'badge-active',
                'fechado': 'badge-inactive'
            };
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
                ${suporte.resposta ? `
                    <p><strong>Resposta:</strong></p>
                    <p style="background: #e8f5e9; padding: 0.8rem; border-radius: 5px;">${escapeHtml(suporte.resposta)}</p>
                ` : ''}
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
            `<tr>
                <td>${new Date(l.data).toLocaleString()}</td>
                <td>${l.evento}</td>
                <td>${l.usuario || '-'}</td>
                <td>${l.ip || '-'}</td>
                <td><span class="badge ${l.gravidade === 'alta' ? 'badge-inactive' : 'badge-active'}">${l.gravidade}</span></td>
            </tr>`
        ).join('');
    } catch(e) { showToast(e.message, 'error'); }
}

// ==================== UTILITÁRIOS ====================
function exportarOngs() { 
    const csv = ongsData.map(o => `${o.id},${o.nome},${o.email},${o.status}`).join('\n'); 
    baixarCSV(csv, 'ongs.csv'); 
}

function exportarLogs() { 
    showToast('Exportação em desenvolvimento', 'info'); 
}

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

function abrirModal(id) { 
    document.getElementById(id).style.display = 'flex'; 
}

function fecharModal(id) { 
    document.getElementById(id).style.display = 'none'; 
}

// ==================== EVENTOS INICIAIS ====================
document.addEventListener('DOMContentLoaded', function() {
    const token = getToken();
    if (!token) { 
        window.location.href = '/login.html'; 
        return; 
    }
    
    // Verificar se é admin
    const userType = localStorage.getItem('userType');
    if (userType !== 'admin') {
        window.location.href = '/';
        return;
    }
    
    // Atualizar nome do admin
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const adminName = document.getElementById('admin-name');
    if (adminName && user.nome) {
        adminName.textContent = user.nome || 'Admin';
    }
    
    // Configurar eventos das abas
    configurarEventosAbas();
    
    // Garantir que a aba Dashboard está visível
    mostrarAba('dashboard');
    
    // Evento de logout
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
        
        if (!resposta || resposta.length < 3) {
            showToast('Resposta deve ter pelo menos 3 caracteres', 'error');
            return;
        }
        
        try {
            await requisicaoApi(`/admin/feedback/${id}`, {
                method: 'PUT',
                body: JSON.stringify({ resposta, status: 'respondido' })
            });
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
        
        if (!resposta || resposta.length < 3) {
            showToast('Resposta deve ter pelo menos 3 caracteres', 'error');
            return;
        }
        
        try {
            await requisicaoApi(`/admin/suporte/${id}`, {
                method: 'PUT',
                body: JSON.stringify({ resposta, status })
            });
            showToast('Solicitação de suporte respondida com sucesso!', 'success');
            fecharModal('modal-responder-suporte');
            carregarSuportesAdmin();
            carregarDashboard();
        } catch(e) { showToast(e.message, 'error'); }
    });
});
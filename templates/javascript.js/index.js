// index.js
const API_BASE_URL = window.location.origin + '/api';
let csrfToken = '';

async function obterCsrfToken() {
    try {
        const response = await fetch(`${API_BASE_URL}/config/csrf-token`);
        if (!response.ok) {
            console.warn('CSRF token não disponível, continuando sem token');
            return;
        }
        const data = await response.json();
        csrfToken = data.csrf_token || '';
    } catch (error) {
        console.warn('Erro ao obter CSRF token:', error);
    }
}

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
    headers['X-CSRF-Token'] = csrfToken;
    return headers;
}

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
        return data;
    } catch (error) {
        console.error('❌ Erro:', error);
        throw error;
    }
}

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
    return apiRequest(`/necessidades${params.toString() ? '?' + params.toString() : ''}`);
}

async function listarEventos() {
    return apiRequest('/eventos');
}

async function listarOngs() {
    return apiRequest('/ongs');
}

async function registrarDoacao(dados) {
    return apiRequest('/doacoes', { method: 'POST', body: JSON.stringify(dados) });
}

async function listarRankingDoadores() {
    return apiRequest('/ranking/doadores?limit=5');
}

async function listarVagasVoluntariado() {
    return apiRequest('/voluntariado/vagas');
}

async function verificarComunicacoesNaoLidas() {
    try {
        const token = getToken();
        if (!token) return;
        const response = await fetch(`${API_BASE_URL}/comunicacoes/nao-lidas`, { headers: getHeaders() });
        if (response.ok) {
            const data = await response.json();
            const naoLidas = data.nao_lidas || 0;
            const badge = document.getElementById('notificacao-badge');
            if (badge) {
                if (naoLidas > 0) {
                    badge.style.display = 'block';
                    badge.textContent = naoLidas > 99 ? '99+' : naoLidas;
                } else {
                    badge.style.display = 'none';
                }
            }
        }
    } catch (error) {
        console.error('Erro ao verificar comunicações:', error);
    }
}

async function carregarComunicacoesUsuario() {
    try {
        const token = getToken();
        if (!token) {
            document.getElementById('comunicacoes-lista').innerHTML = `<div class="empty-state"><p>Faça login para ver suas comunicações</p></div>`;
            return;
        }
        const data = await apiRequest('/comunicacoes');
        const comunicacoes = data.comunicacoes || [];
        const container = document.getElementById('comunicacoes-lista');
        if (comunicacoes.length === 0) {
            container.innerHTML = `<div class="empty-state"><p>📭 Nenhuma comunicação recebida</p></div>`;
            return;
        }
        container.innerHTML = comunicacoes.map(c => {
            const prioridadeColors = { 'normal': '#27ae60', 'alta': '#f39c12', 'urgente': '#e74c3c' };
            const cor = prioridadeColors[c.prioridade] || '#27ae60';
            return `
                <div style="border-left: 4px solid ${cor}; padding: 1rem; margin-bottom: 1rem; background: #f8f9fa; border-radius: 5px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                        <h4 style="color: #2c3e50; margin: 0;">${escapeHtml(c.titulo)}</h4>
                        <span style="background: ${cor}; color: white; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.7rem; font-weight: bold;">${c.prioridade.toUpperCase()}</span>
                    </div>
                    <p style="color: #555; margin: 0.5rem 0; white-space: pre-wrap;">${escapeHtml(c.mensagem)}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
                        <small style="color: #7f8c8d;">📅 ${new Date(c.data_envio).toLocaleString()}</small>
                        <span style="font-size: 0.8rem; color: ${c.lida ? '#27ae60' : '#f39c12'};">${c.lida ? '✅ Lida' : '⏳ Não lida'}</span>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        document.getElementById('comunicacoes-lista').innerHTML = `<p class="error-state">Erro: ${error.message}</p>`;
    }
}

function abrirModalComunicacoes() {
    const modal = document.getElementById('comunicacoes-modal');
    if (modal) {
        modal.style.display = 'flex';
        carregarComunicacoesUsuario();
    }
}

function fecharModalComunicacoes() {
    const modal = document.getElementById('comunicacoes-modal');
    if (modal) modal.style.display = 'none';
}

function abrirChat() {
    const modal = document.getElementById('chat-modal');
    if (modal) {
        modal.style.display = 'flex';
        carregarContatosChat();
    }
}

function fecharChat() {
    const modal = document.getElementById('chat-modal');
    if (modal) modal.style.display = 'none';
}

async function carregarContatosChat() {
    const container = document.getElementById('chat-contatos');
    const token = getToken();
    if (!token) {
        container.innerHTML = '<div class="empty-state"><p>Faça login para usar o chat</p></div>';
        return;
    }
    try {
        const userType = localStorage.getItem('userType');
        let contatos = [];
        if (userType === 'doador') {
            const ongs = await apiRequest('/ongs');
            contatos = ongs.ongs.map(ong => ({ id: ong.id, nome: ong.nome, tipo: 'ong', logo: ong.logo_url || 'https://via.placeholder.com/50?text=ONG' }));
        } else if (userType === 'ong') {
            const doadores = await apiRequest('/admin/doadores');
            contatos = doadores.doadores.map(d => ({ id: d.id, nome: d.nome, tipo: 'doador', logo: 'https://via.placeholder.com/50?text=D' }));
        } else {
            container.innerHTML = '<div class="empty-state"><p>Faça login como doador ou ONG</p></div>';
            return;
        }
        if (contatos.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>Nenhum contato disponível</p></div>';
            return;
        }
        container.innerHTML = contatos.map(contato => `
            <div class="chat-contato" onclick="abrirConversa(${contato.id}, '${contato.tipo}')" style="display: flex; align-items: center; gap: 1rem; padding: 0.8rem; border-bottom: 1px solid #ecf0f1; cursor: pointer; transition: background 0.2s;">
                <img src="${contato.logo}" alt="${escapeHtml(contato.nome)}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;">
                <div><strong>${escapeHtml(contato.nome)}</strong><span style="display: block; font-size: 0.7rem; color: #7f8c8d;">${contato.tipo === 'ong' ? '🏢 ONG' : '👤 Doador'}</span></div>
            </div>
        `).join('');
    } catch (error) {
        container.innerHTML = `<p class="error-state">Erro: ${error.message}</p>`;
    }
}

async function abrirConversa(contatoId, contatoTipo) {
    const token = getToken();
    if (!token) {
        showToast('Faça login para usar o chat', 'warning');
        return;
    }
    try {
        const mensagens = await apiRequest(`/chat/mensagens?com=${contatoId}&com_tipo=${contatoTipo}`);
        const modalContent = document.createElement('div');
        modalContent.className = 'modal';
        modalContent.id = 'conversa-modal';
        modalContent.style.display = 'flex';
        modalContent.innerHTML = `
            <div class="modal-content" style="max-width: 500px; max-height: 80vh;">
                <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3>💬 Conversa</h3>
                    <span class="modal-close" onclick="fecharConversa()" style="cursor: pointer; font-size: 1.5rem; color: #7f8c8d;">&times;</span>
                </div>
                <div id="conversa-mensagens" style="max-height: 300px; overflow-y: auto; margin-bottom: 1rem;">
                    ${mensagens.mensagens.map(m => `
                        <div style="text-align: ${m.is_remetente ? 'right' : 'left'}; margin: 0.5rem 0;">
                            <div style="display: inline-block; background: ${m.is_remetente ? '#27ae60' : '#ecf0f1'}; color: ${m.is_remetente ? 'white' : '#333'}; padding: 0.5rem 1rem; border-radius: 10px; max-width: 80%;">${escapeHtml(m.mensagem)}</div>
                            <div style="font-size: 0.6rem; color: #7f8c8d; margin-top: 0.2rem;">${new Date(m.data).toLocaleString()}</div>
                        </div>
                    `).join('')}
                </div>
                <form id="form-mensagem" style="display: flex; gap: 0.5rem;">
                    <input type="text" id="input-mensagem" placeholder="Digite sua mensagem..." style="flex: 1; padding: 0.5rem; border: 1px solid #ddd; border-radius: 5px;">
                    <button type="submit" class="btn btn-primary" style="padding: 0.5rem 1rem;">Enviar</button>
                </form>
            </div>
        `;
        document.body.appendChild(modalContent);
        document.getElementById('form-mensagem').addEventListener('submit', async (e) => {
            e.preventDefault();
            const mensagem = document.getElementById('input-mensagem').value;
            if (!mensagem) return;
            try {
                await apiRequest('/chat/mensagens', {
                    method: 'POST',
                    body: JSON.stringify({ destinatario_id: contatoId, destinatario_tipo: contatoTipo, mensagem })
                });
                showToast('Mensagem enviada!', 'success');
                document.getElementById('input-mensagem').value = '';
                abrirConversa(contatoId, contatoTipo);
            } catch (error) {
                showToast(error.message, 'error');
            }
        });
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function fecharConversa() {
    const modal = document.getElementById('conversa-modal');
    if (modal) modal.remove();
}

async function carregarRanking() {
    const container = document.getElementById('ranking-container');
    if (!container) return;
    try {
        const data = await listarRankingDoadores();
        const ranking = data.ranking || [];
        if (ranking.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>Nenhum doador no ranking ainda.</p></div>';
            return;
        }
        container.innerHTML = ranking.map((doador, index) => {
            const medalhas = ['🥇', '🥈', '🥉'];
            const medalha = index < 3 ? medalhas[index] : `#${index + 1}`;
            return `
                <div class="ranking-card">
                    <span style="font-size: 2rem; min-width: 50px;">${medalha}</span>
                    <div style="flex: 1;">
                        <strong>${escapeHtml(doador.nome)}</strong>
                        <span style="display: block; font-size: 0.8rem; color: #7f8c8d;">${doador.total_doacoes} doações • ${doador.pontuacao} pontos</span>
                    </div>
                    <div style="background: #27ae60; color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: bold; font-size: 0.9rem;">${doador.pontuacao || 0} pts</div>
                </div>
            `;
        }).join('');
    } catch (error) {
        container.innerHTML = `<div class="error-state"><p>Erro ao carregar ranking: ${error.message}</p></div>`;
    }
}

async function carregarVoluntariado() {
    const container = document.getElementById('voluntariado-container');
    if (!container) return;
    try {
        const data = await listarVagasVoluntariado();
        const vagas = data.vagas || [];
        if (vagas.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>Nenhuma vaga de voluntariado disponível.</p></div>';
            return;
        }
        container.innerHTML = vagas.map(vaga => {
            const dataEvento = new Date(vaga.data_evento);
            const dataFormatada = dataEvento.toLocaleDateString('pt-BR');
            const vagasRestantes = vaga.vagas_disponiveis - vaga.vagas_preenchidas;
            return `
                <div class="voluntariado-card">
                    <h3>${escapeHtml(vaga.titulo)}</h3>
                    <p style="color: #e67e22; font-weight: bold;">🏢 ${escapeHtml(vaga.ong_nome)}</p>
                    <p style="color: #7f8c8d; font-size: 0.85rem;">📅 ${dataFormatada} • 📍 ${escapeHtml(vaga.local || 'Local não informado')}</p>
                    <p style="color: #555; margin: 0.5rem 0;">${escapeHtml(vaga.descricao?.substring(0, 150))}${vaga.descricao?.length > 150 ? '...' : ''}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                        <span style="background: #e8f5e9; color: #27ae60; padding: 0.2rem 0.8rem; border-radius: 20px; font-size: 0.8rem;">${vagasRestantes} vagas disponíveis</span>
                        <button class="btn btn-primary" onclick="abrirModalInscricao(${vaga.id})">🤝 Inscrever-se</button>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        container.innerHTML = `<div class="error-state"><p>Erro: ${error.message}</p></div>`;
    }
}

async function carregarOngs() {
    const container = document.getElementById('ongs-container');
    if (!container) return;
    try {
        const data = await listarOngs();
        const ongs = data.ongs || [];
        if (ongs.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>Nenhuma ONG cadastrada ainda.</p></div>';
            return;
        }
        container.innerHTML = ongs.map(ong => {
            const estrelas = '★'.repeat(Math.round(ong.media_avaliacao || 0)) + '☆'.repeat(5 - Math.round(ong.media_avaliacao || 0));
            return `
                <div class="ong-card" onclick="window.location.href='/perfil_ong.html?id=${ong.id}'" style="cursor: pointer; background: white; border-radius: 15px; padding: 1.5rem; box-shadow: 0 2px 10px rgba(0,0,0,0.1); transition: transform 0.3s;">
                    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                        <img src="${ong.logo_url || 'https://via.placeholder.com/60?text=ONG'}" alt="${escapeHtml(ong.nome)}" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;">
                        <div>
                            <h3 style="margin: 0; color: #2c3e50;">${escapeHtml(ong.nome)}</h3>
                            <p style="margin: 0; color: #7f8c8d; font-size: 0.85rem;">📍 ${escapeHtml(ong.cidade || 'Local não informado')}${ong.uf ? ` - ${ong.uf}` : ''}</p>
                        </div>
                    </div>
                    <p style="color: #555; font-size: 0.9rem; margin-bottom: 0.5rem;">${escapeHtml(ong.descricao?.substring(0, 120))}${ong.descricao?.length > 120 ? '...' : ''}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #f39c12; font-size: 0.9rem;">${estrelas} (${ong.media_avaliacao || 0})</span>
                        <span style="background: #e8f5e9; color: #27ae60; padding: 0.2rem 0.8rem; border-radius: 20px; font-size: 0.8rem;">${ong.total_avaliacoes || 0} avaliações</span>
                    </div>
                </div>
            `;
        }).join('');
        document.querySelectorAll('.ong-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-5px)';
                card.style.boxShadow = '0 5px 20px rgba(0,0,0,0.15)';
            });
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
                card.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
            });
        });
    } catch (error) {
        container.innerHTML = `<div class="error-state"><p>Erro: ${error.message}</p></div>`;
    }
}

let estrelaSelecionada = 0;

function selecionarEstrela(valor) {
    estrelaSelecionada = valor;
    document.getElementById('avaliacao-nota').value = valor;
    const stars = document.querySelectorAll('.star');
    stars.forEach(star => {
        const value = parseInt(star.dataset.value);
        star.textContent = value <= valor ? '★' : '☆';
        star.style.color = value <= valor ? '#f39c12' : '#bdc3c7';
    });
}

function abrirModalAvaliacao(ongId) {
    document.getElementById('avaliacao-ong-id').value = ongId;
    document.getElementById('avaliacao-nota').value = 0;
    document.getElementById('avaliacao-comentario').value = '';
    estrelaSelecionada = 0;
    document.querySelectorAll('.star').forEach(star => {
        star.textContent = '☆';
        star.style.color = '#bdc3c7';
    });
    document.getElementById('avaliacao-modal').style.display = 'flex';
}

function fecharModalAvaliacao() {
    document.getElementById('avaliacao-modal').style.display = 'none';
}

function abrirModalInscricao(vagaId) {
    const token = getToken();
    if (!token) {
        showToast('Faça login para se inscrever', 'warning');
        window.location.href = '/login.html';
        return;
    }
    document.getElementById('inscricao-vaga-id').value = vagaId;
    document.getElementById('inscricao-nome').value = '';
    document.getElementById('inscricao-telefone').value = '';
    document.getElementById('inscricao-mensagem').value = '';
    document.getElementById('inscricao-modal').style.display = 'flex';
}

function fecharModalInscricao() {
    document.getElementById('inscricao-modal').style.display = 'none';
}

// ============================================================
// AUTH - CORRIGIDO
// ============================================================
const auth = {
    isAuthenticated: !!localStorage.getItem('token'),
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    userType: localStorage.getItem('userType'),
    updateUI() {
        const navButtons = document.getElementById('nav-buttons');
        const userMenu = document.getElementById('user-menu');
        const userNameSpan = document.getElementById('user-name');
        const chatIcon = document.getElementById('chat-icon');
        const dashboardLink = document.getElementById('dashboard-link-ong');

        console.log('🔄 Atualizando UI...');
        console.log('🔑 Autenticado:', this.isAuthenticated);
        console.log('👤 Usuário:', this.user);
        console.log('📌 Tipo:', this.userType);

        if (this.isAuthenticated && this.user) {
            // Esconde botões de login/cadastro
            if (navButtons) {
                navButtons.style.display = 'none';
                console.log('✅ Botões de login escondidos');
            }
            
            // Mostra menu do usuário
            if (userMenu) {
                userMenu.style.display = 'flex';
                console.log('✅ Menu do usuário mostrado');
            }
            
            // Mostra nome do usuário
            if (userNameSpan) {
                userNameSpan.textContent = this.user.nome?.split(' ')[0] || 'Usuário';
                console.log('✅ Nome do usuário:', userNameSpan.textContent);
            }
            
            // Mostra ícone do chat
            if (chatIcon) {
                chatIcon.style.display = 'block';
            }
            
            // ============================================================
            // CORREÇÃO: Remove "Dashboard (ONG)" para doadores
            // ============================================================
            if (dashboardLink) {
                if (this.userType === 'doador') {
                    dashboardLink.style.display = 'none';
                    console.log('✅ Dashboard ONG escondido para doador');
                } else {
                    dashboardLink.style.display = 'block';
                    console.log('✅ Dashboard ONG mostrado para ONG');
                }
            }
            
            setTimeout(() => { 
                verificarComunicacoesNaoLidas(); 
                verificarChatNaoLidas(); 
            }, 500);
        } else {
            // Mostra botões de login/cadastro
            if (navButtons) {
                navButtons.style.display = 'flex';
                console.log('✅ Botões de login mostrados');
            }
            
            // Esconde menu do usuário
            if (userMenu) {
                userMenu.style.display = 'none';
                console.log('✅ Menu do usuário escondido');
            }
            
            // Esconde ícone do chat
            if (chatIcon) {
                chatIcon.style.display = 'none';
            }
        }
    },
    setup() {
        console.log('🔧 Configurando autenticação...');
        this.updateUI();
        
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('🚪 Usuário deslogando...');
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

async function verificarChatNaoLidas() {
    try {
        const token = getToken();
        if (!token) return;
        const response = await fetch(`${API_BASE_URL}/chat/nao-lidas`, { headers: getHeaders() });
        if (response.ok) {
            const data = await response.json();
            const naoLidas = data.nao_lidas || 0;
            const badge = document.getElementById('chat-badge');
            if (badge) {
                if (naoLidas > 0) {
                    badge.style.display = 'block';
                    badge.textContent = naoLidas > 99 ? '99+' : naoLidas;
                } else {
                    badge.style.display = 'none';
                }
            }
        }
    } catch (error) {
        console.error('Erro ao verificar chat:', error);
    }
}

let currentPage = 1;
let isLoading = false;
let hasMore = true;
let currentFilters = { cidade: '', categoria: '', status: 'all', busca: '' };

async function carregarEstatisticas() {
    try {
        const stats = await obterEstatisticas();
        document.getElementById('stat-ongs').textContent = stats.total_ongs || 0;
        document.getElementById('stat-doacoes').textContent = stats.total_doacoes || 0;
        document.getElementById('stat-itens').textContent = stats.total_itens || 0;
        document.getElementById('stat-voluntarios').textContent = stats.total_voluntarios || 0;
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
    }
}

async function carregarEventos() {
    const container = document.getElementById('eventos-container');
    if (!container) return;
    try {
        const data = await listarEventos();
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
        container.innerHTML = `<div class="error-message"><p>Erro: ${error.message}</p></div>`;
    }
}

async function carregarNecessidades(append = false) {
    if (isLoading) return;
    isLoading = true;
    const container = document.getElementById('necessidades-container');
    if (!container) { isLoading = false; return; }
    if (!append) container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Carregando necessidades...</p></div>';
    try {
        const params = { cidade: currentFilters.cidade || '', categoria: currentFilters.categoria || '', page: currentPage, limit: 10, busca: currentFilters.busca || '' };
        if (currentFilters.status === 'urgente') params.urgente = 'true';
        const data = await listarNecessidades(params);
        const necessidades = data.necessidades || [];
        hasMore = data.has_more || false;
        if (!append) renderizarNecessidades(necessidades);
        else adicionarNecessidades(necessidades);
        const loadMoreBtn = document.getElementById('btn-load-more');
        if (loadMoreBtn) loadMoreBtn.style.display = hasMore ? 'block' : 'none';
    } catch (error) {
        if (!append) container.innerHTML = `<div class="error-message"><p>Erro: ${error.message}</p><button onclick="location.reload()" class="btn btn-secondary">Tentar Novamente</button></div>`;
    } finally { isLoading = false; }
}

function renderizarNecessidades(necessidades) {
    const container = document.getElementById('necessidades-container');
    if (!container) return;
    if (!necessidades || necessidades.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>🎯 Nenhuma necessidade encontrada</h3><p>Tente ajustar os filtros de busca.</p></div>';
        return;
    }
    container.innerHTML = necessidades.map(nec => criarCardHtml(nec)).join('');
    document.querySelectorAll('.btn-doar').forEach(btn => btn.addEventListener('click', () => abrirModalDoacao(btn.dataset.id)));
    document.querySelectorAll('.btn-avaliar').forEach(btn => btn.addEventListener('click', () => abrirModalAvaliacao(btn.dataset.ongId)));
    document.querySelectorAll('.ong-link').forEach(link => link.addEventListener('click', (e) => { e.stopPropagation(); window.location.href = `/perfil_ong.html?id=${link.dataset.ongId}`; }));
}

function criarCardHtml(nec) {
    const percentual = nec.quantidade_necessaria > 0 ? Math.min((nec.quantidade_recebida / nec.quantidade_necessaria) * 100, 100) : 0;
    const statusClass = nec.urgencia === 'alta' ? 'urgent' : '';
    const mediaAvaliacao = nec.media_avaliacao_ong || 0;
    const estrelas = '★'.repeat(Math.round(mediaAvaliacao)) + '☆'.repeat(5 - Math.round(mediaAvaliacao));
    return `
        <div class="card ${statusClass}">
            ${nec.urgencia === 'alta' ? '<span class="badge-urgente">URGENTE</span>' : ''}
            <h3>${escapeHtml(nec.titulo)}</h3>
            <p class="ong ong-link" data-ong-id="${nec.ong_id}" style="cursor: pointer;">🏢 ${escapeHtml(nec.ong_nome)}</p>
            <p class="endereco">📍 ${escapeHtml(nec.cidade || 'Local não informado')}</p>
            <div class="avaliacao" style="font-size: 0.9rem; color: #f39c12; margin: 0.3rem 0;">${estrelas} (${mediaAvaliacao.toFixed(1)})</div>
            <p class="descricao">${escapeHtml(nec.descricao || '')}</p>
            <div class="progress-section">
                <div class="progress-bar"><div class="progress" style="width: ${percentual}%"></div></div>
                <p class="quantidade">${nec.quantidade_recebida || 0} / ${nec.quantidade_necessaria} itens</p>
            </div>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                <button class="btn-doar" data-id="${nec.id}" style="flex: 1;">Quero Doar</button>
                <button class="btn-avaliar" data-ong-id="${nec.ong_id}" style="flex: 0 1 auto; background: #f39c12; color: white; border: none; padding: 0.8rem 1rem; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">⭐</button>
            </div>
        </div>
    `;
}

function adicionarNecessidades(necessidades) {
    const container = document.getElementById('necessidades-container');
    container.insertAdjacentHTML('beforeend', necessidades.map(nec => criarCardHtml(nec)).join(''));
    document.querySelectorAll('.btn-doar').forEach(btn => btn.addEventListener('click', () => abrirModalDoacao(btn.dataset.id)));
    document.querySelectorAll('.btn-avaliar').forEach(btn => btn.addEventListener('click', () => abrirModalAvaliacao(btn.dataset.ongId)));
    document.querySelectorAll('.ong-link').forEach(link => link.addEventListener('click', (e) => { e.stopPropagation(); window.location.href = `/perfil_ong.html?id=${link.dataset.ongId}`; }));
}

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
        carregarRanking();
        carregarEstatisticas();
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.textContent = textoOriginal;
        submitBtn.disabled = false;
    }
}

async function loadMore() {
    if (!hasMore || isLoading) return;
    currentPage++;
    await carregarNecessidades(true);
}

function handleSearch() {
    currentFilters.cidade = document.getElementById('search-cidade')?.value || '';
    currentFilters.categoria = document.getElementById('search-categoria')?.value || '';
    currentFilters.busca = document.getElementById('search-texto')?.value || '';
    currentPage = 1;
    hasMore = true;
    carregarNecessidades();
}

function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        const navbarHeight = document.querySelector('.header')?.offsetHeight || 70;
        const sectionPosition = section.getBoundingClientRect().top + window.pageYOffset - navbarHeight;
        window.scrollTo({
            top: sectionPosition,
            behavior: 'smooth'
        });
    }
}

function updateActiveNavLink() {
    const sections = ['necessidades', 'ongs-section', 'voluntariado-section', 'ranking-section', 'eventos'];
    const navLinks = document.querySelectorAll('.nav-menu .nav-link');
    
    let currentSection = '';
    sections.forEach(id => {
        const section = document.getElementById(id);
        if (section) {
            const rect = section.getBoundingClientRect();
            if (rect.top <= 150) {
                currentSection = id;
            }
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        const href = link.getAttribute('href');
        if (href === '#' + currentSection) {
            link.classList.add('active');
        }
    });
}

function configurarEventos() {
    const btnBuscar = document.getElementById('btn-buscar');
    const searchCidade = document.getElementById('search-cidade');
    const searchTexto = document.getElementById('search-texto');
    const searchCategoria = document.getElementById('search-categoria');
    const btnLoadMore = document.getElementById('btn-load-more');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const modal = document.getElementById('doacao-modal');
    const closeBtn = document.querySelector('.modal-close');
    const formDoacao = document.getElementById('form-doacao');

    if (btnBuscar) btnBuscar.addEventListener('click', handleSearch);
    if (btnLoadMore) btnLoadMore.addEventListener('click', loadMore);
    if (searchCidade) searchCidade.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSearch(); });
    if (searchTexto) searchTexto.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSearch(); });
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
    
    const formAvaliacao = document.getElementById('form-avaliacao');
    if (formAvaliacao) {
        formAvaliacao.addEventListener('submit', async (e) => {
            e.preventDefault();
            const ongId = document.getElementById('avaliacao-ong-id').value;
            const nota = parseInt(document.getElementById('avaliacao-nota').value);
            const comentario = document.getElementById('avaliacao-comentario').value;
            if (!nota || nota < 1 || nota > 5) {
                showToast('Selecione uma nota de 1 a 5', 'error');
                return;
            }
            try {
                await apiRequest('/avaliacoes', { method: 'POST', body: JSON.stringify({ ong_id: parseInt(ongId), nota, comentario }) });
                showToast('Avaliação enviada com sucesso!', 'success');
                fecharModalAvaliacao();
                carregarNecessidades();
            } catch (error) {
                showToast(error.message, 'error');
            }
        });
    }
    
    const formInscricao = document.getElementById('form-inscricao');
    if (formInscricao) {
        formInscricao.addEventListener('submit', async (e) => {
            e.preventDefault();
            const vagaId = document.getElementById('inscricao-vaga-id').value;
            try {
                await apiRequest(`/voluntariado/vagas/${vagaId}/inscrever`, { method: 'POST', body: JSON.stringify({}) });
                showToast('Inscrição realizada com sucesso!', 'success');
                fecharModalInscricao();
                carregarVoluntariado();
                carregarEstatisticas();
            } catch (error) {
                showToast(error.message, 'error');
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    await obterCsrfToken();
    console.log('🚀 Página carregada!');
    console.log('🔑 Token:', getToken() ? 'Presente' : 'Ausente');
    
    auth.setup();
    carregarEstatisticas();
    carregarEventos();
    carregarNecessidades();
    carregarRanking();
    carregarVoluntariado();
    carregarOngs();
    configurarEventos();
    
    document.addEventListener('scroll', updateActiveNavLink);
    updateActiveNavLink();
    
    setInterval(verificarComunicacoesNaoLidas, 30000);
    setInterval(verificarChatNaoLidas, 30000);
});

window.carregarNecessidades = carregarNecessidades;
window.carregarEventos = carregarEventos;
window.carregarEstatisticas = carregarEstatisticas;
window.carregarRanking = carregarRanking;
window.carregarVoluntariado = carregarVoluntariado;
window.carregarOngs = carregarOngs;
window.loadMore = loadMore;
window.handleSearch = handleSearch;
window.abrirModalDoacao = abrirModalDoacao;
window.fecharModal = fecharModal;
window.abrirModalComunicacoes = abrirModalComunicacoes;
window.fecharModalComunicacoes = fecharModalComunicacoes;
window.abrirChat = abrirChat;
window.fecharChat = fecharChat;
window.abrirConversa = abrirConversa;
window.fecharConversa = fecharConversa;
window.abrirModalAvaliacao = abrirModalAvaliacao;
window.fecharModalAvaliacao = fecharModalAvaliacao;
window.abrirModalInscricao = abrirModalInscricao;
window.fecharModalInscricao = fecharModalInscricao;
window.selecionarEstrela = selecionarEstrela;
window.scrollToSection = scrollToSection;
window.updateActiveNavLink = updateActiveNavLink;
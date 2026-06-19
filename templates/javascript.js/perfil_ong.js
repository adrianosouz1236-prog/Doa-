const API_BASE_URL = window.location.origin + '/api';
let mapInstance = null;

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
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

function getToken() { return localStorage.getItem('token'); }

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

function getOngIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

async function carregarPerfilOng() {
    const ongId = getOngIdFromUrl();
    if (!ongId) {
        showToast('ONG não identificada', 'error');
        window.location.href = '/';
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/ongs/${ongId}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Erro ao carregar perfil');
        }

        document.getElementById('page-title').textContent = `${data.nome} - Doa+`;
        document.getElementById('ong-nome').textContent = data.nome;
        document.getElementById('ong-cidade').textContent = `${data.cidade || ''}${data.uf ? `/${data.uf}` : ''}`;
        document.getElementById('ong-telefone').textContent = data.telefone || 'Não informado';
        document.getElementById('ong-email').textContent = data.email;
        document.getElementById('ong-descricao').textContent = data.descricao || 'Sem descrição disponível.';
        document.getElementById('sobre-texto').textContent = data.descricao || 'Sem descrição disponível.';
        document.getElementById('ong-endereco').textContent = data.endereco || 'Não informado';
        document.getElementById('ong-cidade-uf').textContent = `${data.cidade || ''}${data.uf ? ` - ${data.uf}` : ''}`;
        document.getElementById('ong-endereco-completo').textContent = data.endereco_completo || data.endereco || 'Endereço não informado';
        
        if (data.logo_url) {
            document.getElementById('ong-logo').src = data.logo_url;
        } else {
            document.getElementById('ong-logo').src = 'https://via.placeholder.com/120?text=ONG';
        }

        // Carregar necessidades
        if (data.necessidades && data.necessidades.length > 0) {
            renderizarNecessidades(data.necessidades);
        } else {
            document.getElementById('necessidades-container').innerHTML = '<p>Nenhuma necessidade ativa no momento.</p>';
        }

        // Carregar eventos
        if (data.eventos && data.eventos.length > 0) {
            renderizarEventos(data.eventos);
        } else {
            document.getElementById('eventos-container').innerHTML = '<p>Nenhum evento programado no momento.</p>';
        }

        // Carregar parcerias
        if (data.parcerias && data.parcerias.length > 0) {
            renderizarParcerias(data.parcerias);
        } else {
            document.getElementById('parcerias-container').innerHTML = '<p>Nenhuma parceria registrada.</p>';
        }

        // Carregar fotos
        if (data.fotos && data.fotos.length > 0) {
            renderizarFotos(data.fotos);
        } else {
            document.getElementById('fotos-container').innerHTML = '<p>Nenhuma foto na galeria.</p>';
        }

        // Carregar localização no mapa
        setTimeout(() => {
            inicializarMapa(data.latitude, data.longitude);
        }, 500);

        document.getElementById('loading').style.display = 'none';
        document.getElementById('perfil-content').style.display = 'block';

    } catch (error) {
        console.error('Erro:', error);
        showToast(error.message, 'error');
        document.getElementById('loading').innerHTML = `<p style="color: red;">Erro ao carregar perfil: ${error.message}</p>`;
    }
}

function renderizarNecessidades(necessidades) {
    const container = document.getElementById('necessidades-container');
    container.innerHTML = necessidades.map(nec => {
        const percentual = nec.quantidade_necessaria > 0 
            ? Math.min((nec.quantidade_recebida / nec.quantidade_necessaria) * 100, 100) 
            : 0;
        const urgenciaClass = nec.urgencia === 'alta' ? 'urgente' : '';
        
        return `
            <div class="necessidade-card ${urgenciaClass}">
                <h3>${escapeHtml(nec.titulo)}</h3>
                <span class="categoria">${nec.categoria}</span>
                <p class="descricao">${escapeHtml(nec.descricao?.substring(0, 100))}${nec.descricao?.length > 100 ? '...' : ''}</p>
                <div class="progress-bar">
                    <div class="progress" style="width: ${percentual}%"></div>
                </div>
                <p class="quantidade">${nec.quantidade_recebida || 0} / ${nec.quantidade_necessaria} itens</p>
                <button class="btn-doar" data-id="${nec.id}">Quero Doar</button>
            </div>
        `;
    }).join('');

    document.querySelectorAll('.btn-doar').forEach(btn => {
        btn.addEventListener('click', () => abrirModalDoacao(btn.dataset.id));
    });
}

function renderizarEventos(eventos) {
    const container = document.getElementById('eventos-container');
    container.innerHTML = eventos.map(evento => {
        const dataEvento = new Date(evento.data_evento);
        const dataFormatada = dataEvento.toLocaleDateString('pt-BR');
        const horaFormatada = dataEvento.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        
        return `
            <div class="evento-card">
                <img class="evento-imagem" src="${evento.imagem_url || 'https://via.placeholder.com/400x200?text=Evento'}" alt="${escapeHtml(evento.titulo)}">
                <h3>${escapeHtml(evento.titulo)}</h3>
                <div class="evento-data">📅 ${dataFormatada} • ${horaFormatada}</div>
                <div class="evento-local">📍 ${escapeHtml(evento.local_evento || evento.cidade || 'Local não informado')}</div>
                <p class="evento-descricao">${escapeHtml(evento.descricao?.substring(0, 120))}${evento.descricao?.length > 120 ? '...' : ''}</p>
            </div>
        `;
    }).join('');
}

function renderizarParcerias(parcerias) {
    const container = document.getElementById('parcerias-container');
    container.innerHTML = parcerias.map(par => `
        <div class="parceria-card">
            <img class="parceria-logo" src="${par.logo_url || 'https://via.placeholder.com/80?text=Parceiro'}" alt="${escapeHtml(par.parceiro_nome)}">
            <h3>${escapeHtml(par.parceiro_nome)}</h3>
            <span class="parceria-tipo">${par.tipo_parceria || 'Parceiro'}</span>
            <p class="parceria-descricao">${escapeHtml(par.descricao?.substring(0, 100))}${par.descricao?.length > 100 ? '...' : ''}</p>
            ${par.website_url ? `<a href="${par.website_url}" target="_blank" class="parceria-link">Visitar site →</a>` : ''}
        </div>
    `).join('');
}

function renderizarFotos(fotos) {
    const container = document.getElementById('fotos-container');
    container.innerHTML = fotos.map(foto => `
        <div class="foto-item" onclick="abrirImagem('${foto.foto_url}')">
            <img src="${foto.foto_url}" alt="${escapeHtml(foto.descricao || 'Foto da ONG')}">
            <div class="foto-descricao">${escapeHtml(foto.descricao || 'Sem descrição')}</div>
        </div>
    `).join('');
}

function abrirImagem(url) {
    window.open(url, '_blank');
}

function inicializarMapa(lat, lng) {
    const container = document.getElementById('mapa-container');
    
    if (typeof google === 'undefined' || !google.maps) {
        container.innerHTML = '<p style="text-align: center; padding: 2rem; color: #7f8c8d;">Google Maps não disponível</p>';
        return;
    }
    
    const posicao = { lat: parseFloat(lat) || -23.550520, lng: parseFloat(lng) || -46.633308 };
    
    mapInstance = new google.maps.Map(container, {
        center: posicao,
        zoom: 15,
        mapTypeControl: false,
        streetViewControl: true,
        fullscreenControl: true,
        zoomControl: true
    });
    
    if (lat && lng) {
        new google.maps.Marker({
            position: posicao,
            map: mapInstance,
            title: 'Localização da ONG',
            animation: google.maps.Animation.DROP
        });
    } else {
        container.innerHTML = '<p style="text-align: center; padding: 2rem; color: #7f8c8d;">Localização não informada pela ONG.</p>';
    }
}

// ==================== MODAL DE DOAÇÃO ====================
function abrirModalDoacao(necessidadeId) {
    const token = getToken();
    if (!token) {
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
    
    const token = getToken();
    if (!token) {
        showToast('Faça login para doar', 'warning');
        window.location.href = '/login.html';
        return;
    }

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
        const response = await fetch(`${API_BASE_URL}/doacoes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ necessidade_id: necessidadeId, quantidade, mensagem })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Erro ao registrar doação');
        }

        showToast('Doação registrada com sucesso!', 'success');
        fecharModal();
        setTimeout(() => { window.location.reload(); }, 1500);

    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.textContent = textoOriginal;
        submitBtn.disabled = false;
    }
}

// ==================== ABAS ====================
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
            
            // Redimensionar mapa se for a aba de localização
            if (tabId === 'localizacao' && mapInstance) {
                setTimeout(() => {
                    google.maps.event.trigger(mapInstance, 'resize');
                }, 300);
            }
        });
    });
}

// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', () => {
    setupAuth();
    carregarPerfilOng();
    setupTabs();
    
    const modal = document.getElementById('doacao-modal');
    const closeBtn = document.querySelector('.modal-close');
    
    if (closeBtn) closeBtn.addEventListener('click', fecharModal);
    if (modal) window.addEventListener('click', (e) => { if (e.target === modal) fecharModal(); });
    
    const form = document.getElementById('form-doacao');
    if (form) form.addEventListener('submit', handleDoacaoSubmit);
});
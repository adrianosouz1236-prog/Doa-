const API_BASE_URL = window.location.origin + '/api';
let mapInstance = null;
let markerInstance = null;

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
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
    };
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

function getOngId() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    return user.id;
}

// ==================== DASHBOARD ====================
async function carregarDashboard() {
    try {
        const data = await apiRequest('/ongs/dashboard');
        document.getElementById('stat-necessidades').textContent = data.total_necessidades || 0;
        document.getElementById('stat-doacoes').textContent = data.total_doacoes || 0;
        document.getElementById('stat-itens').textContent = data.total_itens || 0;
        document.getElementById('stat-doadores').textContent = data.total_doadores || 0;
        document.getElementById('stat-eventos').textContent = data.total_eventos || 0;
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
    }
}

// ==================== NECESSIDADES ====================
async function carregarMinhasNecessidades() {
    try {
        const data = await apiRequest('/ongs/necessidades');
        const tbody = document.getElementById('necessidades-tbody');
        if (!data.necessidades || data.necessidades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Nenhuma necessidade cadastrada</td></tr>';
            return;
        }
        tbody.innerHTML = data.necessidades.map(nec => `
            <tr>
                <td>${escapeHtml(nec.titulo)}</td>
                <td><span class="badge badge-info">${nec.categoria}</span></td>
                <td>${nec.quantidade_necessaria}</td>
                <td>${nec.quantidade_recebida || 0}</td>
                <td>${nec.status === 'aberta' ? '<span class="badge badge-success">Ativa</span>' : '<span class="badge badge-warning">Encerrada</span>'}</td>
                <td>
                    <button class="btn btn-outline" style="padding: 0.3rem 0.6rem;" onclick="editarNecessidade(${nec.id})">✏️</button>
                    ${nec.status === 'aberta' ? `<button class="btn btn-danger" style="padding: 0.3rem 0.6rem;" onclick="encerrarNecessidade(${nec.id})">🔚</button>` : ''}
                </td>
            </tr>
        `).join('');
        document.getElementById('necessidades-section').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// FUNÇÕES GLOBAIS PARA ONCLICK - Necessidades
window.abrirModalNecessidade = function(necessidade = null) {
    document.getElementById('necessidade-id').value = '';
    document.getElementById('titulo').value = '';
    document.getElementById('categoria').value = 'alimentos';
    document.getElementById('descricao').value = '';
    document.getElementById('quantidade_necessaria').value = '';
    document.getElementById('urgencia').value = 'media';
    document.getElementById('modal-title').textContent = 'Cadastrar Nova Necessidade';
    abrirModal('necessidade-modal');
};

window.editarNecessidade = async function(id) {
    try {
        const data = await apiRequest(`/ongs/necessidades/${id}`);
        document.getElementById('necessidade-id').value = data.id;
        document.getElementById('titulo').value = data.titulo;
        document.getElementById('categoria').value = data.categoria;
        document.getElementById('descricao').value = data.descricao;
        document.getElementById('quantidade_necessaria').value = data.quantidade_necessaria;
        document.getElementById('urgencia').value = data.urgencia;
        document.getElementById('modal-title').textContent = 'Editar Necessidade';
        abrirModal('necessidade-modal');
    } catch (error) {
        showToast(error.message, 'error');
    }
};

window.encerrarNecessidade = async function(id) {
    if (!confirm('Tem certeza que deseja encerrar esta necessidade?')) return;
    try {
        await apiRequest(`/ongs/necessidades/${id}/encerrar`, { method: 'PUT' });
        showToast('Necessidade encerrada com sucesso!', 'success');
        carregarMinhasNecessidades();
        carregarDashboard();
    } catch (error) {
        showToast(error.message, 'error');
    }
};

// ==================== EVENTOS ====================
window.abrirModalEvento = function() {
    document.getElementById('evento-id').value = '';
    document.getElementById('evento-titulo').value = '';
    document.getElementById('evento-descricao').value = '';
    document.getElementById('evento-data').value = '';
    document.getElementById('evento-local').value = '';
    document.getElementById('evento-endereco').value = '';
    document.getElementById('evento-cidade').value = '';
    document.getElementById('evento-uf').value = '';
    document.getElementById('evento-imagem').value = '';
    abrirModal('evento-modal');
};

window.carregarMeusEventos = async function() {
    try {
        const data = await apiRequest('/ongs/eventos');
        const eventos = data.eventos || [];
        
        if (eventos.length === 0) {
            showToast('Nenhum evento cadastrado', 'info');
            return;
        }
        
        let html = '<div class="cards-grid eventos-grid">';
        eventos.forEach(evento => {
            const dataEvento = new Date(evento.data_evento);
            html += `
                <div class="evento-card">
                    <img class="evento-imagem" src="${evento.imagem_url || 'https://via.placeholder.com/400x200?text=Evento'}" alt="${escapeHtml(evento.titulo)}">
                    <h3>${escapeHtml(evento.titulo)}</h3>
                    <div class="evento-data">📅 ${dataEvento.toLocaleDateString('pt-BR')} • ${dataEvento.toLocaleTimeString('pt-BR')}</div>
                    <div class="evento-local">📍 ${escapeHtml(evento.local_evento || evento.cidade || 'Local não informado')}</div>
                    <p class="evento-descricao">${escapeHtml(evento.descricao?.substring(0, 100))}</p>
                    <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                        <button class="btn btn-outline btn-sm" onclick="editarEvento(${evento.id})">✏️ Editar</button>
                        <button class="btn btn-danger btn-sm" onclick="cancelarEvento(${evento.id})">❌ Cancelar</button>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content';
        modalContent.style.maxWidth = '900px';
        modalContent.style.width = '90%';
        modalContent.innerHTML = `
            <div class="modal-header">
                <h3>Meus Eventos</h3>
                <span class="modal-close" onclick="fecharModalGenerico()">&times;</span>
            </div>
            ${html}
        `;
        
        const modal = document.createElement('div');
        modal.id = 'eventos-list-modal';
        modal.className = 'modal';
        modal.style.display = 'flex';
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        window.fecharModalGenerico = () => {
            modal.remove();
        };
        
    } catch (error) {
        showToast(error.message, 'error');
    }
};

window.editarEvento = async function(id) {
    try {
        const data = await apiRequest('/ongs/eventos');
        const evento = data.eventos?.find(e => e.id == id);
        if (evento) {
            document.getElementById('evento-id').value = evento.id;
            document.getElementById('evento-titulo').value = evento.titulo;
            document.getElementById('evento-descricao').value = evento.descricao || '';
            document.getElementById('evento-data').value = evento.data_evento?.substring(0, 16) || '';
            document.getElementById('evento-local').value = evento.local_evento || '';
            document.getElementById('evento-endereco').value = evento.endereco || '';
            document.getElementById('evento-cidade').value = evento.cidade || '';
            document.getElementById('evento-uf').value = evento.uf || '';
            document.getElementById('evento-imagem').value = evento.imagem_url || '';
            abrirModal('evento-modal');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
};

window.cancelarEvento = async function(id) {
    if (!confirm('Cancelar este evento?')) return;
    try {
        await apiRequest(`/ongs/eventos/${id}`, { method: 'DELETE' });
        showToast('Evento cancelado!', 'success');
        carregarMeusEventos();
        carregarDashboard();
        fecharModal('evento-modal');
    } catch (error) {
        showToast(error.message, 'error');
    }
};

// ==================== PARCERIAS ====================
window.abrirModalParceria = function() {
    document.getElementById('parceria-id').value = '';
    document.getElementById('parceria-nome').value = '';
    document.getElementById('parceria-tipo').value = 'empresa';
    document.getElementById('parceria-descricao').value = '';
    document.getElementById('parceria-logo').value = '';
    document.getElementById('parceria-website').value = '';
    abrirModal('parceria-modal');
};

window.carregarMinhasParcerias = async function() {
    try {
        const data = await apiRequest('/ongs/parcerias');
        const parcerias = data.parcerias || [];
        
        if (parcerias.length === 0) {
            showToast('Nenhuma parceria cadastrada', 'info');
            return;
        }
        
        let html = '<div class="parcerias-grid">';
        parcerias.forEach(par => {
            html += `
                <div class="parceria-card">
                    <img class="parceria-logo" src="${par.logo_url || 'https://via.placeholder.com/80?text=Parceiro'}" alt="${escapeHtml(par.parceiro_nome)}">
                    <h3>${escapeHtml(par.parceiro_nome)}</h3>
                    <span class="parceria-tipo">${par.tipo_parceria || 'Parceiro'}</span>
                    <p class="parceria-descricao">${escapeHtml(par.descricao?.substring(0, 100))}</p>
                    ${par.website_url ? `<a href="${par.website_url}" target="_blank" class="parceria-link">Visitar site →</a>` : ''}
                    <div style="margin-top: 1rem;">
                        <button class="btn btn-outline btn-sm" onclick="editarParceria(${par.id})">✏️ Editar</button>
                        <button class="btn btn-danger btn-sm" onclick="encerrarParceria(${par.id})">❌ Encerrar</button>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content';
        modalContent.style.maxWidth = '900px';
        modalContent.style.width = '90%';
        modalContent.innerHTML = `
            <div class="modal-header">
                <h3>Minhas Parcerias</h3>
                <span class="modal-close" onclick="fecharModalGenerico()">&times;</span>
            </div>
            ${html}
        `;
        
        const modal = document.createElement('div');
        modal.id = 'parcerias-list-modal';
        modal.className = 'modal';
        modal.style.display = 'flex';
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        window.fecharModalGenerico = () => {
            modal.remove();
        };
        
    } catch (error) {
        showToast(error.message, 'error');
    }
};

window.editarParceria = async function(id) {
    try {
        const data = await apiRequest('/ongs/parcerias');
        const parceria = data.parcerias?.find(p => p.id == id);
        if (parceria) {
            document.getElementById('parceria-id').value = parceria.id;
            document.getElementById('parceria-nome').value = parceria.parceiro_nome;
            document.getElementById('parceria-tipo').value = parceria.tipo_parceria || 'empresa';
            document.getElementById('parceria-descricao').value = parceria.descricao || '';
            document.getElementById('parceria-logo').value = parceria.logo_url || '';
            document.getElementById('parceria-website').value = parceria.website_url || '';
            abrirModal('parceria-modal');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
};

window.encerrarParceria = async function(id) {
    if (!confirm('Encerrar esta parceria?')) return;
    try {
        await apiRequest(`/ongs/parcerias/${id}`, { method: 'DELETE' });
        showToast('Parceria encerrada!', 'success');
        carregarMinhasParcerias();
        fecharModal('parceria-modal');
    } catch (error) {
        showToast(error.message, 'error');
    }
};

// ==================== DOAÇÕES ====================
window.carregarDoacoesRecebidas = async function() {
    try {
        const data = await apiRequest('/ongs/doacoes');
        const tbody = document.getElementById('doacoes-tbody');
        if (!data.doacoes || data.doacoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Nenhuma doação recebida</td></tr>';
            return;
        }
        tbody.innerHTML = data.doacoes.map(doc => `
            <tr>
                <td>${new Date(doc.data).toLocaleDateString('pt-BR')}</td>
                <td>${escapeHtml(doc.doador_nome || 'Anônimo')}</td>
                <td>${escapeHtml(doc.necessidade_titulo)}</td>
                <td>${doc.quantidade}</td>
                <td><span class="badge ${doc.status === 'confirmada' ? 'badge-success' : 'badge-warning'}">${doc.status || 'Pendente'}</span></td>
                <td>${doc.status !== 'confirmada' ? `<button class="btn btn-primary" style="padding: 0.3rem 0.6rem;" onclick="confirmarDoacao(${doc.id})">✓ Confirmar</button>` : '-'}</td>
            </tr>
        `).join('');
        document.getElementById('doacoes-section').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        showToast(error.message, 'error');
    }
};

window.confirmarDoacao = async function(id) {
    if (!confirm('Confirmar esta doação?')) return;
    try {
        await apiRequest(`/ongs/doacoes/${id}/confirmar`, { method: 'PUT' });
        showToast('Doação confirmada!', 'success');
        carregarDoacoesRecebidas();
        carregarDashboard();
    } catch (error) {
        showToast(error.message, 'error');
    }
};

// ==================== PERFIL ====================
window.carregarPerfilOng = async function() {
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
        
        const userName = document.getElementById('user-name');
        if (userName) {
            userName.textContent = (data.nome || 'ONG').split(' ')[0];
        }
        
        abrirModal('perfil-modal');
    } catch (error) {
        showToast(error.message, 'error');
    }
};

// ==================== FOTOS DA ONG ====================
window.carregarFotosOng = async function() {
    try {
        const data = await apiRequest('/ongs/fotos');
        const fotos = data.fotos || [];
        
        const container = document.getElementById('fotos-lista');
        if (fotos.length === 0) {
            container.innerHTML = '<p style="color: #7f8c8d;">Nenhuma foto cadastrada. Adicione até 3 fotos da sua ONG.</p>';
        } else {
            container.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1rem;">
                    ${fotos.map(f => `
                        <div style="position: relative; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <img src="${f.foto_url}" alt="${escapeHtml(f.descricao || 'Foto da ONG')}" style="width: 100%; height: 150px; object-fit: cover;">
                            <p style="padding: 0.5rem; font-size: 0.8rem; text-align: center;">${escapeHtml(f.descricao || 'Sem descrição')}</p>
                            <button class="btn btn-danger btn-sm" style="position: absolute; top: 5px; right: 5px; padding: 0.2rem 0.5rem;" onclick="removerFoto(${f.id})">✕</button>
                        </div>
                    `).join('')}
                </div>
                <p style="color: #7f8c8d; margin-top: 0.5rem; font-size: 0.8rem;">${fotos.length}/3 fotos</p>
            `;
        }
        
        document.getElementById('foto-url').value = '';
        document.getElementById('foto-descricao').value = '';
        abrirModal('fotos-modal');
    } catch (error) {
        showToast(error.message, 'error');
    }
};

window.removerFoto = async function(fotoId) {
    if (!confirm('Remover esta foto?')) return;
    try {
        await apiRequest(`/ongs/fotos/${fotoId}`, { method: 'DELETE' });
        showToast('Foto removida!', 'success');
        carregarFotosOng();
    } catch (error) {
        showToast(error.message, 'error');
    }
};

// ==================== LOCALIZAÇÃO DA ONG ====================
window.carregarLocalizacaoOng = async function() {
    try {
        const data = await apiRequest('/ongs/localizacao');
        document.getElementById('loc-endereco').value = data.endereco_completo || data.endereco || '';
        document.getElementById('loc-latitude').value = data.latitude || '';
        document.getElementById('loc-longitude').value = data.longitude || '';
        document.getElementById('loc-search').value = '';
        
        abrirModal('localizacao-modal');
        
        setTimeout(() => {
            inicializarMapa(data.latitude, data.longitude);
        }, 300);
    } catch (error) {
        showToast(error.message, 'error');
    }
};

function inicializarMapa(lat, lng) {
    const container = document.getElementById('mapa-container');
    
    if (typeof google === 'undefined' || !google.maps) {
        container.innerHTML = '<p style="text-align: center; padding: 2rem; color: #7f8c8d;">Carregando Google Maps...</p>';
        return;
    }
    
    const posicao = { lat: parseFloat(lat) || -23.550520, lng: parseFloat(lng) || -46.633308 };
    
    mapInstance = new google.maps.Map(container, {
        center: posicao,
        zoom: 15,
        mapTypeControl: false,
        streetViewControl: true,
        fullscreenControl: true
    });
    
    if (lat && lng) {
        markerInstance = new google.maps.Marker({
            position: posicao,
            map: mapInstance,
            title: 'Localização da ONG',
            draggable: true,
            animation: google.maps.Animation.DROP
        });
        
        markerInstance.addListener('dragend', function() {
            const pos = markerInstance.getPosition();
            document.getElementById('loc-latitude').value = pos.lat();
            document.getElementById('loc-longitude').value = pos.lng();
            mostrarEnderecoPorCoordenadas(pos.lat(), pos.lng());
        });
    } else {
        mapInstance.addListener('click', function(e) {
            if (markerInstance) {
                markerInstance.setPosition(e.latLng);
            } else {
                markerInstance = new google.maps.Marker({
                    position: e.latLng,
                    map: mapInstance,
                    draggable: true,
                    animation: google.maps.Animation.DROP
                });
                
                markerInstance.addListener('dragend', function() {
                    const pos = markerInstance.getPosition();
                    document.getElementById('loc-latitude').value = pos.lat();
                    document.getElementById('loc-longitude').value = pos.lng();
                    mostrarEnderecoPorCoordenadas(pos.lat(), pos.lng());
                });
            }
            document.getElementById('loc-latitude').value = e.latLng.lat();
            document.getElementById('loc-longitude').value = e.latLng.lng();
            mostrarEnderecoPorCoordenadas(e.latLng.lat(), e.latLng.lng());
        });
    }
}

function mostrarEnderecoPorCoordenadas(lat, lng) {
    if (typeof google === 'undefined' || !google.maps) return;
    
    const geocoder = new google.maps.Geocoder();
    geocoder.geocode({ location: { lat: lat, lng: lng } }, (results, status) => {
        if (status === 'OK' && results[0]) {
            document.getElementById('loc-endereco').value = results[0].formatted_address;
        }
    });
}

window.buscarLocalizacao = function() {
    const search = document.getElementById('loc-search').value;
    if (!search) {
        showToast('Digite um endereço para buscar', 'warning');
        return;
    }
    
    if (typeof google === 'undefined' || !google.maps) {
        showToast('Google Maps não está disponível', 'error');
        return;
    }
    
    const geocoder = new google.maps.Geocoder();
    geocoder.geocode({ address: search }, (results, status) => {
        if (status === 'OK' && results[0]) {
            const location = results[0].geometry.location;
            const lat = location.lat();
            const lng = location.lng();
            
            document.getElementById('loc-latitude').value = lat;
            document.getElementById('loc-longitude').value = lng;
            document.getElementById('loc-endereco').value = results[0].formatted_address;
            
            if (mapInstance) {
                mapInstance.setCenter({ lat, lng });
                mapInstance.setZoom(16);
                
                if (markerInstance) {
                    markerInstance.setPosition({ lat, lng });
                } else {
                    markerInstance = new google.maps.Marker({
                        position: { lat, lng },
                        map: mapInstance,
                        draggable: true,
                        animation: google.maps.Animation.DROP
                    });
                    
                    markerInstance.addListener('dragend', function() {
                        const pos = markerInstance.getPosition();
                        document.getElementById('loc-latitude').value = pos.lat();
                        document.getElementById('loc-longitude').value = pos.lng();
                        mostrarEnderecoPorCoordenadas(pos.lat(), pos.lng());
                    });
                }
            }
        } else {
            showToast('Endereço não encontrado', 'error');
        }
    });
};

window.obterLocalizacaoAtual = function() {
    if (!navigator.geolocation) {
        showToast('Geolocalização não suportada pelo navegador', 'error');
        return;
    }
    
    showToast('Obtendo localização...', 'info');
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            document.getElementById('loc-latitude').value = lat;
            document.getElementById('loc-longitude').value = lng;
            mostrarEnderecoPorCoordenadas(lat, lng);
            
            if (mapInstance) {
                mapInstance.setCenter({ lat, lng });
                mapInstance.setZoom(16);
                
                if (markerInstance) {
                    markerInstance.setPosition({ lat, lng });
                } else {
                    markerInstance = new google.maps.Marker({
                        position: { lat, lng },
                        map: mapInstance,
                        draggable: true,
                        animation: google.maps.Animation.DROP
                    });
                    
                    markerInstance.addListener('dragend', function() {
                        const pos = markerInstance.getPosition();
                        document.getElementById('loc-latitude').value = pos.lat();
                        document.getElementById('loc-longitude').value = pos.lng();
                        mostrarEnderecoPorCoordenadas(pos.lat(), pos.lng());
                    });
                }
            }
        },
        (error) => {
            showToast('Erro ao obter localização: ' + error.message, 'error');
        },
        { enableHighAccuracy: true }
    );
};

// ==================== UTILITÁRIOS ====================
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function abrirModal(id) { document.getElementById(id).style.display = 'flex'; }
function fecharModal(id) { document.getElementById(id).style.display = 'none'; }

// Função chamada pelo Google Maps
function initMap() {
    console.log('Google Maps carregado!');
}

// ==================== EVENT LISTENERS ====================
document.addEventListener('DOMContentLoaded', () => {
    const token = getToken();
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    if (!token || !user.id) { 
        window.location.href = '/login.html'; 
        return; 
    }
    
    const userType = localStorage.getItem('userType');
    if (userType !== 'ong') {
        window.location.href = '/';
        return;
    }
    
    const userNameSpan = document.getElementById('user-name');
    if (userNameSpan && user.nome) {
        userNameSpan.textContent = user.nome.split(' ')[0];
    }
    
    carregarDashboard();
    carregarMinhasNecessidades();
    carregarDoacoesRecebidas();
    
    // Necessidade form
    document.getElementById('necessidade-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('necessidade-id').value;
        const dados = {
            titulo: document.getElementById('titulo').value,
            categoria: document.getElementById('categoria').value,
            descricao: document.getElementById('descricao').value,
            quantidade_necessaria: parseInt(document.getElementById('quantidade_necessaria').value),
            urgencia: document.getElementById('urgencia').value
        };
        try {
            if (id) {
                await apiRequest(`/ongs/necessidades/${id}`, { method: 'PUT', body: JSON.stringify(dados) });
                showToast('Necessidade atualizada!', 'success');
            } else {
                await apiRequest('/ongs/necessidades', { method: 'POST', body: JSON.stringify(dados) });
                showToast('Necessidade cadastrada!', 'success');
            }
            fecharModal('necessidade-modal');
            carregarMinhasNecessidades();
            carregarDashboard();
        } catch (error) { showToast(error.message, 'error'); }
    });
    
    // Evento form
    document.getElementById('evento-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('evento-id').value;
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
            if (id) {
                await apiRequest(`/ongs/eventos/${id}`, { method: 'PUT', body: JSON.stringify(dados) });
                showToast('Evento atualizado!', 'success');
            } else {
                await apiRequest('/ongs/eventos', { method: 'POST', body: JSON.stringify(dados) });
                showToast('Evento cadastrado!', 'success');
            }
            fecharModal('evento-modal');
            carregarDashboard();
        } catch (error) { showToast(error.message, 'error'); }
    });
    
    // Parceria form
    document.getElementById('parceria-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('parceria-id').value;
        const dados = {
            parceiro_nome: document.getElementById('parceria-nome').value,
            tipo_parceria: document.getElementById('parceria-tipo').value,
            descricao: document.getElementById('parceria-descricao').value,
            logo_url: document.getElementById('parceria-logo').value,
            website_url: document.getElementById('parceria-website').value
        };
        try {
            if (id) {
                await apiRequest(`/ongs/parcerias/${id}`, { method: 'PUT', body: JSON.stringify(dados) });
                showToast('Parceria atualizada!', 'success');
            } else {
                await apiRequest('/ongs/parcerias', { method: 'POST', body: JSON.stringify(dados) });
                showToast('Parceria adicionada!', 'success');
            }
            fecharModal('parceria-modal');
            carregarDashboard();
        } catch (error) { showToast(error.message, 'error'); }
    });
    
    // Perfil form
    document.getElementById('perfil-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const dados = {
            nome: document.getElementById('ong-nome').value,
            email: document.getElementById('ong-email').value,
            telefone: document.getElementById('ong-telefone').value,
            endereco: document.getElementById('ong-endereco').value,
            cidade: document.getElementById('ong-cidade').value,
            uf: document.getElementById('ong-uf').value,
            descricao: document.getElementById('ong-descricao').value,
            logo_url: document.getElementById('ong-logo').value
        };
        try {
            await apiRequest('/ongs/perfil', { method: 'PUT', body: JSON.stringify(dados) });
            showToast('Perfil atualizado!', 'success');
            fecharModal('perfil-modal');
        } catch (error) { showToast(error.message, 'error'); }
    });
    
    // Fotos form
    document.getElementById('fotos-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const dados = {
            foto_url: document.getElementById('foto-url').value,
            descricao: document.getElementById('foto-descricao').value
        };
        try {
            await apiRequest('/ongs/fotos', { method: 'POST', body: JSON.stringify(dados) });
            showToast('Foto adicionada!', 'success');
            carregarFotosOng();
        } catch (error) { showToast(error.message, 'error'); }
    });
    
    // Localização form
    document.getElementById('localizacao-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const dados = {
            latitude: parseFloat(document.getElementById('loc-latitude').value),
            longitude: parseFloat(document.getElementById('loc-longitude').value),
            endereco_completo: document.getElementById('loc-endereco').value
        };
        
        if (!dados.latitude || !dados.longitude) {
            showToast('Selecione uma localização no mapa', 'warning');
            return;
        }
        
        try {
            await apiRequest('/ongs/localizacao', { method: 'PUT', body: JSON.stringify(dados) });
            showToast('Localização atualizada!', 'success');
            fecharModal('localizacao-modal');
        } catch (error) { showToast(error.message, 'error'); }
    });
    
    // Logout
    document.getElementById('logout-btn').addEventListener('click', () => {
        localStorage.clear();
        window.location.href = '/';
    });
});

// Exportar funções para uso global
window.initMap = initMap;
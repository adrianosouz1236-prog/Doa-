const API_BASE_URL = window.location.origin + '/api';

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

// ==================== AUTENTICAÇÃO ====================
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

// ==================== DATA DE CONSENTIMENTO ====================
function atualizarDataConsentimento() {
    const dataElement = document.getElementById('data-consentimento');
    if (dataElement) {
        const hoje = new Date();
        const dataFormatada = hoje.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
        dataElement.textContent = dataFormatada;
    }
}

// ==================== BAIXAR COMPROVANTE ====================
async function baixarComprovanteConsentimento() {
    try {
        const token = getToken();
        if (!token) {
            showToast('Faça login para baixar o comprovante', 'warning');
            window.location.href = '/login.html';
            return;
        }

        // Buscar dados do usuário
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Erro ao buscar dados do usuário');
        }

        const user = await response.json();

        // Gerar comprovante
        const comprovante = `
            ============================================
            COMPROVANTE DE CONSENTIMENTO - LGPD
            ============================================
            
            Data: ${new Date().toLocaleString('pt-BR')}
            
            DADOS DO USUÁRIO:
            Nome: ${user.nome || 'Não informado'}
            Email: ${user.email || 'Não informado'}
            Tipo: ${user.tipo || 'Não informado'}
            
            CONSENTIMENTO:
            ✓ Concordo com a Política de Privacidade
            ✓ Autorizo o tratamento dos meus dados
            ✓ Estou ciente dos meus direitos (LGPD)
            
            FINALIDADES:
            • Operação da plataforma Doa+
            • Processamento de doações
            • Comunicação sobre doações
            • Melhoria dos serviços
            
            COMPARTILHAMENTO:
            • PagSeguro (processamento de pagamentos)
            • ONGs (informações de doações)
            • Autoridades legais (quando exigido)
            
            ---------------------------
            Assinatura: ${user.nome || 'Usuário'}
            IP: ${window.location.hostname}
            ============================================
        `;

        // Criar e baixar arquivo
        const blob = new Blob([comprovante], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `consentimento_lgpd_${new Date().toISOString().slice(0,10)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showToast('Comprovante baixado com sucesso!', 'success');

    } catch (error) {
        showToast('Erro ao baixar comprovante: ' + error.message, 'error');
    }
}

// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', () => {
    setupAuth();
    atualizarDataConsentimento();

    // Evento para baixar comprovante
    const btnDownload = document.querySelector('.btn-download-consentimento');
    if (btnDownload) {
        btnDownload.addEventListener('click', baixarComprovanteConsentimento);
    }
});

// Exportar funções
window.baixarComprovanteConsentimento = baixarComprovanteConsentimento;
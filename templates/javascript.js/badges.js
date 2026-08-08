/* ============================================================
   BADGES DE SEGURANÇA - Doa+
   Scripts para interação com os selos de segurança
   ============================================================ */

// ===== CONFIGURAÇÕES =====
const BADGE_CONFIG = {
    SSL: {
        text: 'SSL Secure',
        icon: '🔒',
        tooltip: 'Conexão criptografada com SSL/TLS. Seus dados estão seguros.',
        class: 'badge-ssl'
    },
    LGPD: {
        text: 'LGPD Compliant',
        icon: '🔐',
        tooltip: 'Em conformidade com a Lei Geral de Proteção de Dados (LGPD).',
        class: 'badge-lgpd'
    },
    PAGAMENTO: {
        text: 'Pagamento Seguro',
        icon: '💳',
        tooltip: 'Pagamentos processados com criptografia e segurança de ponta.',
        class: 'badge-pagamento'
    },
    DOACAO: {
        text: 'Doação Segura',
        icon: '🛡️',
        tooltip: 'Sua doação é protegida com as melhores práticas de segurança.',
        class: 'badge-doacao'
    },
    OPENSOURCE: {
        text: 'Open Source',
        icon: '📦',
        tooltip: 'Código aberto e transparente. Verifique no GitHub.',
        class: 'badge-opensource'
    },
    RESPONSIVO: {
        text: 'Responsivo',
        icon: '📱',
        tooltip: 'Acesse de qualquer dispositivo: computador, tablet ou celular.',
        class: 'badge-responsive'
    }
};

// ===== FUNÇÃO PARA CRIAR BADGE =====
function criarBadge(tipo, tamanho = 'md', comTooltip = true, animado = false) {
    const config = BADGE_CONFIG[tipo];
    if (!config) return '';
    
    const tamanhos = {
        sm: 'badge-sm',
        md: '',
        lg: 'badge-lg'
    };
    
    const classeTamanho = tamanhos[tamanho] || '';
    const classeAnimado = animado ? 'badge-pulse' : '';
    const classeTooltip = comTooltip ? 'badge-tooltip' : '';
    const classeLink = config.link ? 'badge-security-link' : '';
    
    return `
        <span class="badge-security ${config.class} ${classeTamanho} ${classeAnimado} ${classeTooltip} ${classeLink}" 
              ${config.link ? `onclick="window.open('${config.link}', '_blank')"` : ''}
              ${config.id ? `id="${config.id}"` : ''}>
            <span class="badge-icon">${config.icon}</span>
            <span class="badge-text">${config.text}</span>
            ${comTooltip ? `<span class="tooltip-text">${config.tooltip}</span>` : ''}
        </span>
    `;
}

// ===== FUNÇÃO PARA CRIAR TODOS OS BADGES =====
function criarBadgesCompleto(containerId, opcoes = {}) {
    const {
        tipos = ['SSL', 'LGPD', 'PAGAMENTO', 'DOACAO'],
        tamanho = 'md',
        comTooltip = true,
        animado = false,
        containerClass = 'security-badges-container'
    } = opcoes;
    
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`Container #${containerId} não encontrado.`);
        return '';
    }
    
    container.className = containerClass;
    
    let html = '';
    tipos.forEach(tipo => {
        html += criarBadge(tipo, tamanho, comTooltip, animado);
    });
    
    container.innerHTML = html;
    return html;
}

// ===== FUNÇÃO PARA ADICIONAR BADGES NO RODAPÉ =====
function adicionarBadgesRodape(opcoes = {}) {
    const {
        tipos = ['SSL', 'LGPD', 'PAGAMENTO', 'OPENSOURCE'],
        tamanho = 'sm',
        comTooltip = true,
        animado = true
    } = opcoes;
    
    let container = document.querySelector('.footer-badges');
    
    if (!container) {
        const footer = document.querySelector('.footer');
        if (!footer) {
            console.warn('Rodapé não encontrado. Adicionando badges no final da página.');
            const body = document.querySelector('body');
            const div = document.createElement('div');
            div.className = 'footer-badges';
            div.style.cssText = 'display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; padding: 1rem; background: #f8f9fa;';
            body.appendChild(div);
            container = div;
        } else {
            const div = document.createElement('div');
            div.className = 'footer-badges';
            footer.appendChild(div);
            container = div;
        }
    }
    
    let html = '';
    tipos.forEach(tipo => {
        html += criarBadge(tipo, tamanho, comTooltip, animado);
    });
    
    container.innerHTML = html;
    return html;
}

// ===== FUNÇÃO PARA ATUALIZAR BADGES DINAMICAMENTE =====
function atualizarBadges(containerId, novosTipos) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`Container #${containerId} não encontrado.`);
        return;
    }
    
    let html = '';
    novosTipos.forEach(tipo => {
        html += criarBadge(tipo, 'md', true, true);
    });
    
    container.innerHTML = html;
}

// ===== FUNÇÃO PARA VERIFICAR SSL =====
function verificarSSL() {
    if (window.location.protocol === 'https:') {
        const badges = document.querySelectorAll('.badge-ssl');
        badges.forEach(badge => {
            badge.style.background = 'linear-gradient(135deg, #27ae60, #2ecc71)';
            badge.innerHTML = `
                <span class="badge-icon">🔒</span>
                <span class="badge-text">SSL Ativo</span>
                <span class="tooltip-text">Conexão criptografada com SSL/TLS. Seus dados estão seguros.</span>
            `;
        });
        return true;
    } else {
        const badges = document.querySelectorAll('.badge-ssl');
        badges.forEach(badge => {
            badge.style.background = 'linear-gradient(135deg, #27ae60, #2ecc71)';
            badge.innerHTML = `
                <span class="badge-icon">🔒</span>
                <span class="badge-text">SSL Ativo</span>
                <span class="tooltip-text">Conexão criptografada com SSL/TLS. Seus dados estão seguros.</span>
            `;
        });
        return true;
    }
}

// ===== INICIALIZAÇÃO AUTOMÁTICA =====
document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.security-badges-container');
    if (container) {
        verificarSSL();
    }
});

window.criarBadge = criarBadge;
window.criarBadgesCompleto = criarBadgesCompleto;
window.adicionarBadgesRodape = adicionarBadgesRodape;
window.atualizarBadges = atualizarBadges;
window.verificarSSL = verificarSSL;
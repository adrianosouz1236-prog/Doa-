// cadastro_ong.js - COM CAMPOS BANCÁRIOS SEPARADOS
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = toast.querySelector('.toast-message');
    toastMessage.textContent = message;
    toast.className = `toast toast-${type}`;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3000);
}

const API_BASE_URL = window.location.origin + '/api';

async function obterCsrfToken() {
    try {
        const response = await fetch(`${API_BASE_URL}/config/csrf-token`);
        const data = await response.json();
        document.getElementById('csrf-token').value = data.csrf_token || '';
    } catch (error) {
        console.error('Erro ao obter CSRF token:', error);
    }
}

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
        container.style.color = '#7f8c8d';
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

// Mostrar campo "Outro banco"
document.addEventListener('DOMContentLoaded', function() {
    const bancoSelect = document.getElementById('banco');
    const outroBanco = document.getElementById('outro-banco');
    
    if (bancoSelect) {
        bancoSelect.addEventListener('change', function() {
            if (this.value === 'outro') {
                outroBanco.style.display = 'block';
            } else {
                outroBanco.style.display = 'none';
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', async () => {
    await obterCsrfToken();
    const form = document.getElementById('cadastro-ong-form');
    const senhaInput = document.getElementById('senha');
    if (senhaInput) {
        senhaInput.addEventListener('input', function() { atualizarForcaSenha(this.value); });
    }
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const consentimento = document.getElementById('consentimento-lgpd').checked;
            if (!consentimento) {
                showToast('É obrigatório concordar com a Política de Privacidade e Termos de Serviço.', 'error');
                return;
            }
            
            // Coletar dados do formulário
            const banco = document.getElementById('banco').value;
            let nomeBanco = banco;
            if (banco === 'outro') {
                nomeBanco = document.getElementById('outro_banco_nome').value;
                if (!nomeBanco) {
                    showToast('Informe o nome do banco', 'error');
                    return;
                }
            }
            
            const dados = {
                nome: document.getElementById('nome').value,
                cnpj: document.getElementById('cnpj').value,
                email: document.getElementById('email').value,
                senha: document.getElementById('senha').value,
                telefone: document.getElementById('telefone').value,
                endereco: document.getElementById('endereco').value,
                cidade: document.getElementById('cidade').value,
                uf: document.getElementById('uf').value,
                descricao: document.getElementById('descricao').value,
                // Dados bancários separados
                banco: nomeBanco,
                agencia: document.getElementById('agencia').value,
                conta: document.getElementById('conta').value,
                tipo_conta: document.getElementById('tipo_conta').value,
                consentimento_lgpd: consentimento
            };
            
            // Validar dados bancários (se algum campo de banco foi preenchido, todos devem estar)
            const temBanco = dados.banco || dados.agencia || dados.conta;
            if (temBanco) {
                if (!dados.banco || !dados.agencia || !dados.conta) {
                    showToast('Para cadastrar conta bancária, preencha Banco, Agência e Conta.', 'error');
                    return;
                }
            }
            
            const submitBtn = e.target.querySelector('button[type="submit"]');
            const textoOriginal = submitBtn.textContent;
            submitBtn.textContent = 'Cadastrando...';
            submitBtn.disabled = true;
            
            try {
                const response = await fetch(`${API_BASE_URL}/auth/cadastro/ong`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': document.getElementById('csrf-token').value
                    },
                    body: JSON.stringify(dados)
                });
                const data = await response.json();
                if (!response.ok) {
                    if (data.detalhes) throw new Error(data.error + ': ' + data.detalhes.join(', '));
                    throw new Error(data.error || 'Erro no cadastro');
                }
                showToast('ONG cadastrada com sucesso! Faça login para continuar.', 'success');
                setTimeout(() => { window.location.href = '/login.html'; }, 2000);
            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                submitBtn.textContent = textoOriginal;
                submitBtn.disabled = false;
            }
        });
    }
});

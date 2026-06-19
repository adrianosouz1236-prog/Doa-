
        function showToast(message, type = 'info') {
            const toast = document.getElementById('toast');
            const toastMessage = toast.querySelector('.toast-message');
            
            toastMessage.textContent = message;
            toast.className = `toast toast-${type}`;
            toast.style.display = 'block';
            
            setTimeout(() => {
                toast.style.display = 'none';
            }, 3000);
        }

        const API_BASE_URL = window.location.origin + '/api';

        document.addEventListener('DOMContentLoaded', () => {
            const form = document.getElementById('cadastro-ong-form');
            if (form) {
                form.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    const dados = {
                        nome: document.getElementById('nome').value,
                        cnpj: document.getElementById('cnpj').value,
                        email: document.getElementById('email').value,
                        senha: document.getElementById('senha').value,
                        telefone: document.getElementById('telefone').value,
                        endereco: document.getElementById('endereco').value,
                        cidade: document.getElementById('cidade').value,
                        uf: document.getElementById('uf').value,
                        descricao: document.getElementById('descricao').value
                    };
                    
                    const submitBtn = e.target.querySelector('button[type="submit"]');
                    const textoOriginal = submitBtn.textContent;
                    submitBtn.textContent = 'Cadastrando...';
                    submitBtn.disabled = true;
                    
                    try {
                        const response = await fetch(`${API_BASE_URL}/auth/cadastro/ong`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(dados)
                        });
                        
                        const data = await response.json();
                        
                        if (!response.ok) {
                            throw new Error(data.error || 'Erro no cadastro');
                        }
                        
                        showToast('ONG cadastrada com sucesso! Faça login para continuar.', 'success');
                        
                        setTimeout(() => {
                            window.location.href = '/login.html';
                        }, 2000);
                        
                    } catch (error) {
                        showToast(error.message, 'error');
                    } finally {
                        submitBtn.textContent = textoOriginal;
                        submitBtn.disabled = false;
                    }
                });
            }
        });
    
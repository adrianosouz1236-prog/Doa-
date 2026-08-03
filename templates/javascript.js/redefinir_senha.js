  // ============================================================
        //  VARIÁVEIS
        // ============================================================
        const API_BASE_URL = window.location.origin + '/api';
        const urlParams = new URLSearchParams(window.location.search);
        const email = urlParams.get('email');
        const token = urlParams.get('token');

        // ============================================================
        //  INICIALIZAÇÃO
        // ============================================================
        document.addEventListener('DOMContentLoaded', function() {
            if (email) {
                document.getElementById('emailDisplay').textContent = email;
                document.getElementById('userInfo').style.display = 'block';
            }

            // Valida senha enquanto digita
            document.getElementById('novaSenha').addEventListener('input', function() {
                validarRequisitosSenha(this.value);
                atualizarForcaSenha(this.value);
            });

            // Enter para submit
            document.getElementById('confirmarSenha').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') redefinirSenha();
            });
        });

        // ============================================================
        //  MENSAGENS
        // ============================================================
        function showError(message) {
            const errorDiv = document.getElementById('errorMessage');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            document.getElementById('successMessage').style.display = 'none';
            setTimeout(() => { errorDiv.style.display = 'none'; }, 5000);
        }

        function showSuccess(message) {
            const successDiv = document.getElementById('successMessage');
            successDiv.textContent = message;
            successDiv.style.display = 'block';
            document.getElementById('errorMessage').style.display = 'none';
        }

        // ============================================================
        //  MOSTRAR/OCULTAR SENHA
        // ============================================================
        function togglePassword(fieldId) {
            const field = document.getElementById(fieldId);
            const icon = field.parentElement.querySelector('.toggle-password i');
            if (field.type === 'password') {
                field.type = 'text';
                icon.className = 'fas fa-eye-slash';
            } else {
                field.type = 'password';
                icon.className = 'fas fa-eye';
            }
        }

        // ============================================================
        //  VALIDAÇÃO DE SENHA
        // ============================================================
        function validarRequisitosSenha(senha) {
            const requisitos = [
                { id: 'req-comprimento', test: senha.length >= 12, msg: 'Mínimo de 12 caracteres' },
                { id: 'req-maiuscula', test: /[A-Z]/.test(senha), msg: 'Pelo menos 1 letra maiúscula' },
                { id: 'req-minuscula', test: /[a-z]/.test(senha), msg: 'Pelo menos 1 letra minúscula' },
                { id: 'req-numero', test: /\d/.test(senha), msg: 'Pelo menos 1 número' },
                { id: 'req-especial', test: /[!@#$%^&*(),.?":{}|<>]/.test(senha), msg: 'Pelo menos 1 caractere especial' }
            ];

            requisitos.forEach(req => {
                const el = document.getElementById(req.id);
                if (el) {
                    el.className = req.test ? 'valid' : 'invalid';
                    el.textContent = (req.test ? '✅' : '❌') + ' ' + req.msg;
                }
            });

            const invalidos = requisitos.filter(r => !r.test);
            return {
                valido: invalidos.length === 0,
                invalidos: invalidos
            };
        }

        function atualizarForcaSenha(senha) {
            const result = validarRequisitosSenha(senha);
            const fill = document.getElementById('strengthFill');
            const text = document.getElementById('strengthText');
            const feedback = document.getElementById('passwordFeedback');

            if (!senha) {
                fill.style.width = '0%';
                text.textContent = '';
                feedback.textContent = '';
                return;
            }

            const total = 5;
            const validos = total - result.invalidos.length;
            const score = (validos / total) * 5;
            let nivel, cor;

            if (score >= 4.5) { nivel = 'Forte'; cor = 'strong'; }
            else if (score >= 3.5) { nivel = 'Boa'; cor = 'good'; }
            else if (score >= 2.5) { nivel = 'Média'; cor = 'medium'; }
            else { nivel = 'Fraca'; cor = 'weak'; }

            fill.className = `strength-fill ${cor}`;
            fill.style.width = `${(score / 5) * 100}%`;
            text.textContent = `Força da senha: ${nivel}`;
            text.className = `strength-text ${cor}`;

            if (result.valido) {
                feedback.textContent = '✅ Senha atende a todos os requisitos!';
                feedback.style.color = '#27ae60';
            } else {
                const faltam = result.invalidos.map(r => r.msg).join(', ');
                feedback.textContent = `⚠️ Faltam: ${faltam}`;
                feedback.style.color = '#e74c3c';
            }
        }

        // ============================================================
        //  GERAR SENHA FORTE
        // ============================================================
        function gerarSenhaForte() {
            const caracteres = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()';
            let senha = '';
            const comprimento = 16;

            const tipos = [
                'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                'abcdefghijklmnopqrstuvwxyz',
                '0123456789',
                '!@#$%^&*()'
            ];

            tipos.forEach(tipo => {
                senha += tipo.charAt(Math.floor(Math.random() * tipo.length));
            });

            for (let i = 4; i < comprimento; i++) {
                senha += caracteres.charAt(Math.floor(Math.random() * caracteres.length));
            }

            senha = senha.split('').sort(() => Math.random() - 0.5).join('');

            document.getElementById('novaSenha').value = senha;
            document.getElementById('confirmarSenha').value = senha;
            document.getElementById('senhaGeradaDisplay').textContent = senha;
            validarRequisitosSenha(senha);
            atualizarForcaSenha(senha);
            showSuccess('Senha forte gerada! Clique em "Redefinir Senha" para salvar.');
        }

        // ============================================================
        //  REDEFINIR SENHA
        // ============================================================
        async function redefinirSenha() {
            const novaSenha = document.getElementById('novaSenha').value;
            const confirmarSenha = document.getElementById('confirmarSenha').value;

            if (!novaSenha) {
                showError('Digite uma nova senha');
                return;
            }

            if (novaSenha !== confirmarSenha) {
                showError('As senhas não coincidem');
                return;
            }

            const result = validarRequisitosSenha(novaSenha);
            if (!result.valido) {
                const faltam = result.invalidos.map(r => r.msg).join(', ');
                showError(`Senha fraca: ${faltam}`);
                return;
            }

            const btn = event.target;
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Redefinindo...';

            try {
                const payload = {
                    nova_senha: novaSenha
                };

                if (email) payload.email = email;
                if (token) payload.codigo = token;

                const response = await fetch(`${API_BASE_URL}/auth/recuperar-senha/redefinir`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const resultData = await response.json();

                if (resultData.success) {
                    showSuccess('✅ Senha redefinida com sucesso! Redirecionando para o login...');
                    setTimeout(() => {
                        window.location.href = '/login.html';
                    }, 3000);
                } else {
                    showError(resultData.error || 'Erro ao redefinir senha');
                }
            } catch (error) {
                showError('Erro de conexão. Tente novamente.');
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }
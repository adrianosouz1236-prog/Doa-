  // ============================================================
        //  VARIÁVEIS GLOBAIS
        // ============================================================
        let currentEmail = '';
        let currentTokenId = null;
        let timerInterval = null;
        let timeLeft = 0;
        const API_BASE_URL = window.location.origin + '/api';

        // ============================================================
        //  MENSAGENS
        // ============================================================
        function showError(message) {
            const errorDiv = document.getElementById('errorMessage');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            document.getElementById('successMessage').style.display = 'none';
            document.getElementById('infoMessage').style.display = 'none';
            setTimeout(() => { errorDiv.style.display = 'none'; }, 5000);
        }

        function showSuccess(message) {
            const successDiv = document.getElementById('successMessage');
            successDiv.textContent = message;
            successDiv.style.display = 'block';
            document.getElementById('errorMessage').style.display = 'none';
            document.getElementById('infoMessage').style.display = 'none';
        }

        function showInfo(message) {
            const infoDiv = document.getElementById('infoMessage');
            infoDiv.textContent = message;
            infoDiv.style.display = 'block';
            document.getElementById('errorMessage').style.display = 'none';
            document.getElementById('successMessage').style.display = 'none';
            setTimeout(() => { infoDiv.style.display = 'none'; }, 8000);
        }

        // ============================================================
        //  NAVEGAÇÃO ENTRE ETAPAS
        // ============================================================
        function nextStep(step) {
            document.querySelectorAll('.form-step').forEach(form => form.classList.remove('active'));
            document.getElementById(`step${step}Form`).classList.add('active');

            document.querySelectorAll('.step').forEach((stepEl, index) => {
                if (index + 1 < step) {
                    stepEl.classList.add('completed');
                    stepEl.classList.remove('active');
                } else if (index + 1 === step) {
                    stepEl.classList.add('active');
                    stepEl.classList.remove('completed');
                } else {
                    stepEl.classList.remove('active', 'completed');
                }
            });
        }

        // ============================================================
        //  TIMER
        // ============================================================
        function startTimer(minutes = 15) {
            if (timerInterval) clearInterval(timerInterval);
            timeLeft = minutes * 60;
            updateTimerDisplay();

            timerInterval = setInterval(() => {
                if (timeLeft <= 0) {
                    clearInterval(timerInterval);
                    document.getElementById('timer').innerHTML =
                        '<span class="expired"><i class="fas fa-exclamation-circle"></i> Código expirado. Solicite um novo.</span>';
                } else {
                    timeLeft--;
                    updateTimerDisplay();
                }
            }, 1000);
        }

        function updateTimerDisplay() {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            document.getElementById('timer').innerHTML =
                `<i class="fas fa-hourglass-half"></i> Código válido por: ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
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
        //  VALIDAÇÃO DE SENHA (CLIENTE)
        // ============================================================
        function validarRequisitosSenha(senha) {
            const requisitos = [
                { id: 'req-comprimento', test: senha.length >= 12, msg: 'Mínimo de 12 caracteres' },
                { id: 'req-maiuscula', test: /[A-Z]/.test(senha), msg: 'Pelo menos 1 letra maiúscula' },
                { id: 'req-minuscula', test: /[a-z]/.test(senha), msg: 'Pelo menos 1 letra minúscula' },
                { id: 'req-numero', test: /\d/.test(senha), msg: 'Pelo menos 1 número' },
                { id: 'req-especial', test: /[!@#$%^&*(),.?":{}|<>]/.test(senha), msg: 'Pelo menos 1 caractere especial' }
            ];

            const validos = requisitos.filter(r => r.test);
            const invalidos = requisitos.filter(r => !r.test);

            // Atualiza lista de requisitos
            requisitos.forEach(req => {
                const el = document.getElementById(req.id);
                if (el) {
                    el.className = req.test ? 'valid' : 'invalid';
                    el.textContent = (req.test ? '✅' : '❌') + ' ' + req.msg;
                }
            });

            return {
                valido: invalidos.length === 0,
                total: requisitos.length,
                validos: validos.length,
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

            const score = (result.validos / result.total) * 5;
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

        // Valida enquanto digita
        document.addEventListener('DOMContentLoaded', function() {
            const novaSenha = document.getElementById('novaSenha');
            if (novaSenha) {
                novaSenha.addEventListener('input', function() {
                    atualizarForcaSenha(this.value);
                });
            }
        });

        // ============================================================
        //  GERAR SENHA FORTE
        // ============================================================
        function gerarSenhaForte() {
            const caracteres = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()';
            let senha = '';
            const comprimento = 16;

            // Garante pelo menos um de cada tipo
            const tipos = [
                'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                'abcdefghijklmnopqrstuvwxyz',
                '0123456789',
                '!@#$%^&*()'
            ];

            tipos.forEach(tipo => {
                senha += tipo.charAt(Math.floor(Math.random() * tipo.length));
            });

            // Preenche o resto
            for (let i = 4; i < comprimento; i++) {
                senha += caracteres.charAt(Math.floor(Math.random() * caracteres.length));
            }

            // Embaralha
            senha = senha.split('').sort(() => Math.random() - 0.5).join('');

            document.getElementById('novaSenha').value = senha;
            document.getElementById('confirmarSenha').value = senha;
            document.getElementById('senhaGeradaDisplay').textContent = senha;
            atualizarForcaSenha(senha);
            showSuccess('Senha forte gerada! Clique em "Redefinir Senha" para salvar.');
        }

        // ============================================================
        //  ETAPA 1: SOLICITAR RECUPERAÇÃO
        // ============================================================
        async function solicitarRecuperacao() {
            const email = document.getElementById('email').value.trim();

            if (!email) {
                showError('Digite seu e-mail');
                return;
            }

            if (!email.includes('@') || !email.includes('.')) {
                showError('Digite um e-mail válido');
                return;
            }

            const btn = event.target;
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';

            try {
                const response = await fetch(`${API_BASE_URL}/auth/recuperar-senha/solicitar`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email })
                });

                const result = await response.json();

                if (result.success) {
                    currentEmail = email;
                    showSuccess(result.message || 'Código enviado para seu e-mail!');

                    if (result.codigo) {
                        showInfo(`🔑 Modo desenvolvimento - Seu código: <strong>${result.codigo}</strong>`);
                    }

                    startTimer(15);
                    nextStep(2);
                } else {
                    showError(result.error || 'Erro ao solicitar recuperação');
                }
            } catch (error) {
                showError('Erro de conexão. Tente novamente.');
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }

        // ============================================================
        //  REENVIAR CÓDIGO
        // ============================================================
        async function reenviarCodigo() {
            if (!currentEmail) {
                showError('E-mail não encontrado. Volte ao passo 1.');
                return;
            }

            const link = event.target;
            const originalText = link.textContent;
            link.textContent = 'Enviando...';
            link.style.pointerEvents = 'none';

            try {
                const response = await fetch(`${API_BASE_URL}/auth/recuperar-senha/solicitar`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: currentEmail })
                });

                const result = await response.json();

                if (result.success) {
                    showSuccess('Novo código enviado para seu e-mail!');
                    startTimer(15);

                    if (result.codigo) {
                        showInfo(`🔑 Modo desenvolvimento - Novo código: <strong>${result.codigo}</strong>`);
                    }
                } else {
                    showError(result.error || 'Erro ao reenviar código');
                }
            } catch (error) {
                showError('Erro de conexão. Tente novamente.');
            } finally {
                link.textContent = originalText;
                link.style.pointerEvents = 'auto';
            }
        }

        // ============================================================
        //  ETAPA 2: VERIFICAR CÓDIGO
        // ============================================================
        async function verificarCodigo() {
            const codigo = document.getElementById('codigo').value.trim();

            if (!codigo || codigo.length !== 6) {
                showError('Digite o código de 6 dígitos');
                return;
            }

            if (!/^\d{6}$/.test(codigo)) {
                showError('O código deve conter apenas números');
                return;
            }

            const btn = event.target;
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verificando...';

            try {
                const response = await fetch(`${API_BASE_URL}/auth/recuperar-senha/verificar`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: currentEmail, codigo: codigo })
                });

                const result = await response.json();

                if (result.success) {
                    currentTokenId = result.token_id;
                    showSuccess('Código verificado! Agora escolha uma nova senha.');
                    nextStep(3);
                } else {
                    showError(result.error || 'Código inválido ou expirado');
                }
            } catch (error) {
                showError('Erro de conexão. Tente novamente.');
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }

        // ============================================================
        //  ETAPA 3: REDEFINIR SENHA
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

            // Valida força da senha
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
                const response = await fetch(`${API_BASE_URL}/auth/recuperar-senha/redefinir`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: currentEmail,
                        nova_senha: novaSenha,
                        token_id: currentTokenId
                    })
                });

                const result = await response.json();

                if (result.success) {
                    showSuccess('✅ Senha redefinida com sucesso! Redirecionando para o login...');
                    setTimeout(() => {
                        window.location.href = '/login.html';
                    }, 3000);
                } else {
                    showError(result.error || 'Erro ao redefinir senha');
                }
            } catch (error) {
                showError('Erro de conexão. Tente novamente.');
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }

        // ============================================================
        //  ENTER PARA SUBMIT
        // ============================================================
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('email').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') solicitarRecuperacao();
            });

            document.getElementById('codigo').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') verificarCodigo();
            });

            document.getElementById('confirmarSenha').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') redefinirSenha();
            });
        });
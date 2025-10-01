document.addEventListener('DOMContentLoaded', function() {
    // =========================================================
    // MAPEAMENTO DE ELEMENTOS DO DOM
    // =========================================================
    const UIElements = {
        bancaAtual: document.getElementById('banca-atual'),
        stakeMax: document.getElementById('stake-max'),
        apostasHoje: document.getElementById('apostas-hoje'),
        alertaRisco: document.getElementById('alerta-risco'),
        tabelaBody: document.querySelector('#tabela-apostas tbody'),
        dataHoje: document.getElementById('data-hoje'),
        chatInput: document.getElementById('chat-input'),
        configBancaInicial: document.getElementById('config-banca-inicial'),
        configMetaMinima: document.getElementById('config-meta-minima'),
        configStakeMax: document.getElementById('config-stake-max'),
        btnChatEnviar: document.getElementById('btn-chat-enviar'),
        btnConfigurarBanca: document.getElementById('btn-configurar-banca'),
        btnRegistrarAposta: document.getElementById('btn-registrar-aposta'),
        btnReset: document.getElementById('reset-button'),
        btnTipsTab: document.getElementById('btn-tips-tab'),
        btnGestaoTab: document.getElementById('btn-gestao-tab'),
        tipsTab: document.getElementById('tips-tab'),
        gestaoTab: document.getElementById('gestao-tab'),
        tipChat: document.getElementById('tip-chat'),
        inputStake: document.getElementById('input-stake'),
        inputOdd: document.getElementById('input-odd'),
        inputResultado: document.getElementById('input-resultado'),
        inputAcrescimo: document.getElementById('input-acrescimo')
    };

    // =========================================================
    // VARIÁVEIS DE ESTADO
    // =========================================================
    let bancaAtual = 0.00, apostasHoje = 0;
    let resultadosDoDia = [], apostasRegistradas = [];
    let chatState = 'initial', jogoParaAnalisar = {};
    let BANCA_INICIAL = 30.00, META_MINIMA = 200.00, TETO_MAXIMO_STAKE = 3.00;
    const LIMITE_APOSTAS_DIARIO = 10, LIMITE_RED_SEQUENCIAL = 3;

    // =========================================================
    // LÓGICA DA ABA DE ANÁLISE (TIPS) COM API
    // =========================================================
    function appendMessage(sender, message) {
        const msgEl = document.createElement('p');
        msgEl.className = sender === 'bot' ? 'bot-message' : 'user-message';
        msgEl.innerHTML = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        UIElements.tipChat.appendChild(msgEl);
        UIElements.tipChat.scrollTop = UIElements.tipChat.scrollHeight;
    }

    async function processarComando() {
        const comando = UIElements.chatInput.value.trim();
        if (comando === '') return;
        appendMessage('user', comando);
        UIElements.chatInput.value = '';

        if (chatState === 'initial' && comando.toLowerCase().includes('quero apostar')) {
            appendMessage('bot', "Excelente! Qual jogo você quer analisar? Use o formato **'Time A vs Time B'**.");
            chatState = 'waiting_game';
        } else if (chatState === 'waiting_game') {
            const times = comando.split(/ vs | x /i);
            if (times.length !== 2) {
                appendMessage('bot', "Formato inválido. Por favor, use **'Time A vs Time B'**.");
                return;
            }
            jogoParaAnalisar.time_casa = times[0].trim();
            jogoParaAnalisar.time_fora = times[1].trim();
            appendMessage('bot', `Entendido. E qual o campeonato para **${jogoParaAnalisar.time_casa} vs ${jogoParaAnalisar.time_fora}**?`);
            chatState = 'waiting_league';
        } else if (chatState === 'waiting_league') {
            jogoParaAnalisar.campeonato = comando;
            appendMessage('bot', `Ok. Buscando e analisando dados para **${jogoParaAnalisar.time_casa} vs ${jogoParaAnalisar.time_fora}**. Aguarde...`);
            
            try {
               const response = await fetch('/analisar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(jogoParaAnalisar ),
                });

                if (!response.ok) throw new Error('O servidor retornou um erro.');
                const analise = await response.json();
                
                appendMessage('bot', '--- 📊 **ANÁLISE CONCLUÍDA** 📊 ---');
                if (analise.melhor_aposta) {
                    const best = analise.melhor_aposta;
                    appendMessage('bot', `**MELHOR ENTRADA IDENTIFICADA:**`);
                    appendMessage('bot', `<strong>Mercado:</strong> ${best.mercado}  
<strong>Entrada:</strong> ${best.entrada}  
<strong>Odd Estimada:</strong> ${best.odd}`);
                    appendMessage('bot', `<strong>Justificativa:</strong> <em>${best.justificativa}</em>`);
                }
                if (analise.outras_opcoes && analise.outras_opcoes.length > 0) {
                    appendMessage('bot', `--- 💡 **OUTRAS OPÇÕES DE VALOR** ---`);
                    analise.outras_opcoes.forEach(opt => {
                         appendMessage('bot', `<strong>Mercado:</strong> ${opt.mercado}  
<strong>Entrada:</strong> ${opt.entrada} (${opt.odd})`);
                    });
                }
            } catch (error) {
                console.error('Erro ao contatar a API:', error);
                appendMessage('bot', 'Desculpe, não consegui conectar ao servidor de análise. Verifique se o `servidor.py` está rodando.');
            } finally {
                chatState = 'initial';
                jogoParaAnalisar = {};
                appendMessage('bot', "Análise finalizada. Digite **'Quero Apostar'** para um novo jogo.");
            }
        } else {
            appendMessage('bot', "Comando não reconhecido. Digite **'Quero Apostar'** para iniciar.");
        }
    }

    // =========================================================
    // LÓGICA DA GESTÃO DE BANCA (FUNÇÕES ANTERIORES)
    // =========================================================
    function getTodayDate() { return new Date().toLocaleDateString('pt-BR'); }

    function salvarDados() {
        const dados = {
            apostas: apostasRegistradas,
            config: { bancaInicial: BANCA_INICIAL, metaMinima: META_MINIMA, stakeMaxima: TETO_MAXIMO_STAKE }
        };
        localStorage.setItem('gestaoBancaData', JSON.stringify(dados));
    }

    function carregarDados() {
        const dadosSalvos = localStorage.getItem('gestaoBancaData');
        if (dadosSalvos) {
            const dados = JSON.parse(dadosSalvos);
            apostasRegistradas = dados.apostas || [];
            const config = dados.config || {};
            BANCA_INICIAL = config.bancaInicial || 30.00;
            META_MINIMA = config.metaMinima || 200.00;
            TETO_MAXIMO_STAKE = config.stakeMaxima || 3.00;
        }
        UIElements.configBancaInicial.value = BANCA_INICIAL.toFixed(2);
        UIElements.configMetaMinima.value = META_MINIMA.toFixed(2);
        UIElements.configStakeMax.value = TETO_MAXIMO_STAKE.toFixed(2);
        recalcularBanca();
        atualizarUI();
    }

    function resetarDados() {
        if (confirm(`ATENÇÃO: Resetar todos os dados? A banca voltará para R$ ${BANCA_INICIAL.toFixed(2)}.`)) {
            apostasRegistradas = [];
            salvarDados();
            recalcularBanca();
            atualizarUI();
            alert("Dados resetados com sucesso!");
        }
    }

    function configurarBanca() {
        BANCA_INICIAL = parseFloat(UIElements.configBancaInicial.value) || BANCA_INICIAL;
        META_MINIMA = parseFloat(UIElements.configMetaMinima.value) || META_MINIMA;
        TETO_MAXIMO_STAKE = parseFloat(UIElements.configStakeMax.value) || TETO_MAXIMO_STAKE;
        salvarDados();
        recalcularBanca();
        atualizarUI();
        alert("Configurações aplicadas!");
    }

    function adicionarAposta() {
        const stake = parseFloat(UIElements.inputStake.value);
        const odd = parseFloat(UIElements.inputOdd.value);
        const resultado = UIElements.inputResultado.value;
        const acrescimo = parseFloat(UIElements.inputAcrescimo.value) || 0.00;

        if (!stake || !odd || !resultado) return alert("Preencha Stake, Odd e Resultado.");
        if (stake > TETO_MAXIMO_STAKE && !confirm(`Stake (R$ ${stake.toFixed(2)}) maior que o teto (R$ ${TETO_MAXIMO_STAKE.toFixed(2)}). Continuar?`)) return;
        
        apostasRegistradas.push({ id: Date.now(), data: getTodayDate(), stake, odd, resultado, acrescimo });
        salvarDados();
        recalcularBanca();
        atualizarUI();
        UIElements.inputStake.value = UIElements.inputOdd.value = UIElements.inputResultado.value = '';
        UIElements.inputAcrescimo.value = '0.00';
    }

    function resolverAposta(apostaId, novoResultado) {
        const aposta = apostasRegistradas.find(a => a.id === apostaId);
        if (aposta) {
            aposta.resultado = novoResultado;
            salvarDados();
            recalcularBanca();
            atualizarUI();
        }
    }

    function recalcularBanca() {
        let tempBanca = BANCA_INICIAL;
        resultadosDoDia = [];
        const hoje = getTodayDate();
        apostasRegistradas.forEach(aposta => {
            if (aposta.resultado !== 'pending') {
                const ganhoPerda = (aposta.resultado === 'win') ? aposta.stake * (aposta.odd - 1) + aposta.acrescimo : -aposta.stake;
                tempBanca += ganhoPerda;
                if (aposta.data === hoje) resultadosDoDia.push(aposta.resultado);
            }
        });
        bancaAtual = tempBanca;
        apostasHoje = apostasRegistradas.filter(a => a.data === hoje).length;
    }

    function atualizarUI() {
        UIElements.bancaAtual.textContent = `R$ ${bancaAtual.toFixed(2)}`;
        UIElements.stakeMax.textContent = `R$ ${TETO_MAXIMO_STAKE.toFixed(2)}`;
        UIElements.apostasHoje.textContent = `${apostasHoje}/${LIMITE_APOSTAS_DIARIO}`;
        UIElements.dataHoje.textContent = getTodayDate();
        renderizarTabela();
        verificarAlertas();
    }

    function renderizarTabela() {
        UIElements.tabelaBody.innerHTML = '';
        let bancaFlutuante = BANCA_INICIAL;
        apostasRegistradas.forEach((aposta, index) => {
            const newRow = UIElements.tabelaBody.insertRow();
            let ganhoPerdaDisplay = '---', bancaFinalDisplay = 'PENDENTE';
            if (aposta.resultado !== 'pending') {
                const ganhoPerda = (aposta.resultado === 'win') ? aposta.stake * (aposta.odd - 1) + aposta.acrescimo : -aposta.stake;
                bancaFlutuante += ganhoPerda;
                ganhoPerdaDisplay = ganhoPerda.toFixed(2);
                bancaFinalDisplay = bancaFlutuante.toFixed(2);
            }
            const values = [aposta.data, index + 1, aposta.stake.toFixed(2), aposta.odd.toFixed(2), aposta.resultado.toUpperCase(), ganhoPerdaDisplay, aposta.acrescimo.toFixed(2), bancaFinalDisplay, ''];
            const labels = ["Data", "# do Dia", "Stake (R$)", "Odd", "Resultado", "Ganho/Perda", "Acréscimo", "Banca Final", "Ação"];
            values.forEach((value, i) => {
                let cell = newRow.insertCell(i);
                cell.setAttribute('data-label', labels[i]);
                cell.textContent = value;
            });
            newRow.cells[4].classList.add(aposta.resultado);
            if (aposta.resultado === 'pending') {
                const actionCell = newRow.cells[8];
                const btnWin = document.createElement('button');
                btnWin.textContent = 'WIN';
                btnWin.className = 'btn-fechar';
                btnWin.onclick = () => resolverAposta(aposta.id, 'win');
                const btnRed = document.createElement('button');
                btnRed.textContent = 'RED';
                btnRed.className = 'btn-fechar';
                btnRed.onclick = () => resolverAposta(aposta.id, 'red');
                actionCell.appendChild(btnWin);
                actionCell.appendChild(btnRed);
            }
        });
    }

    function verificarAlertas() {
        UIElements.alertaRisco.className = 'alerta';
        UIElements.alertaRisco.textContent = '';
        if (apostasHoje >= LIMITE_APOSTAS_DIARIO) {
            UIElements.alertaRisco.className = 'alerta ativo alerta-limite';
            UIElements.alertaRisco.textContent = '⚠️ LIMITE DIÁRIO ATINGIDO. PARE!';
        } else if (resultadosDoDia.slice(-LIMITE_RED_SEQUENCIAL).every(r => r === 'red') && resultadosDoDia.length >= LIMITE_RED_SEQUENCIAL) {
            UIElements.alertaRisco.className = 'alerta ativo alerta-stop';
            UIElements.alertaRisco.textContent = `🚨 STOP LOSS! ${LIMITE_RED_SEQUENCIAL} REDs seguidos.`;
        } else if (bancaAtual >= META_MINIMA) {
            UIElements.alertaRisco.className = 'alerta ativo alerta-limite';
            UIElements.alertaRisco.textContent = `🏆 PARABÉNS! META ATINGIDA!`;
        }
    }

    function openTab(tabName) {
        UIElements.tipsTab.style.display = (tabName === 'tips') ? 'block' : 'none';
        UIElements.gestaoTab.style.display = (tabName === 'gestao') ? 'block' : 'none';
        UIElements.btnTipsTab.classList.toggle('active', tabName === 'tips');
        UIElements.btnGestaoTab.classList.toggle('active', tabName === 'gestao');
    }

    // =========================================================
    // INICIALIZAÇÃO E EVENTOS
    // =========================================================
    function init() {
        UIElements.btnTipsTab.addEventListener('click', () => openTab('tips'));
        UIElements.btnGestaoTab.addEventListener('click', () => openTab('gestao'));
        UIElements.btnChatEnviar.addEventListener('click', processarComando);
        UIElements.chatInput.addEventListener('keyup', (e) => { if (e.key === 'Enter') processarComando(); });
        UIElements.btnConfigurarBanca.addEventListener('click', configurarBanca);
        UIElements.btnRegistrarAposta.addEventListener('click', adicionarAposta);
        UIElements.btnReset.addEventListener('click', resetarDados);
        carregarDados();
        openTab('tips');
    }

    init();
});

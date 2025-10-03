document.addEventListener('DOMContentLoaded', function() {
    // =========================================================
    // MAPEAMENTO DE ELEMENTOS DO DOM
    // =========================================================
    const UIElements = {
        // Abas e Botões de Abas
        btnFutebolTab: document.getElementById('btn-futebol-tab'),
        btnNflTab: document.getElementById('btn-nfl-tab'),
        btnNbaTab: document.getElementById('btn-nba-tab'),
        btnGestaoTab: document.getElementById('btn-gestao-tab'),
        futebolTab: document.getElementById('futebol-tab'),
        nflTab: document.getElementById('nfl-tab'),
        nbaTab: document.getElementById('nba-tab'),
        gestaoTab: document.getElementById('gestao-tab'),
        // Chats e Inputs de Análise
        chats: {
            futebol: { chat: document.getElementById('tip-chat-futebol'), input: document.getElementById('chat-input-futebol'), btn: document.getElementById('btn-chat-enviar-futebol') },
            nfl: { chat: document.getElementById('tip-chat-nfl'), input: document.getElementById('chat-input-nfl'), btn: document.getElementById('btn-chat-enviar-nfl') },
            nba: { chat: document.getElementById('tip-chat-nba'), input: document.getElementById('chat-input-nba'), btn: document.getElementById('btn-chat-enviar-nba') },
        },
        // Gestão de Banca
        bancaAtual: document.getElementById('banca-atual'),
        stakeMax: document.getElementById('stake-max'),
        apostasHoje: document.getElementById('apostas-hoje'),
        alertaRisco: document.getElementById('alerta-risco'),
        tabelaBody: document.querySelector('#tabela-apostas tbody'),
        dataHoje: document.getElementById('data-hoje'),
        configBancaInicial: document.getElementById('config-banca-inicial'),
        configMetaMinima: document.getElementById('config-meta-minima'),
        configStakeMax: document.getElementById('config-stake-max'),
        btnConfigurarBanca: document.getElementById('btn-configurar-banca'),
        btnRegistrarAposta: document.getElementById('btn-registrar-aposta'),
        btnReset: document.getElementById('reset-button'),
        inputStake: document.getElementById('input-stake'),
        inputOdd: document.getElementById('input-odd'),
        inputResultado: document.getElementById('input-resultado'),
        inputAcrescimo: document.getElementById('input-acrescimo'),
    };

    // =========================================================
    // VARIÁVEIS DE ESTADO
    // =========================================================
    let chatStates = { futebol: 'initial', nfl: 'initial', nba: 'initial' };
    let jogoParaAnalisar = {};
    let esporteAtivo = 'futebol';
    let bancaAtual = 0.00, apostasHoje = 0, resultadosDoDia = [], apostasRegistradas = [];
    let BANCA_INICIAL = 30.00, META_MINIMA = 200.00, TETO_MAXIMO_STAKE = 3.00;
    const LIMITE_APOSTAS_DIARIO = 10, LIMITE_RED_SEQUENCIAL = 3;

    // =========================================================
    // LÓGICA DE ANÁLISE (TIPS) COM API
    // =========================================================
    function appendMessage(esporte, sender, message) {
        const chatEl = UIElements.chats[esporte].chat;
        const msgEl = document.createElement('p');
        msgEl.className = sender === 'bot' ? 'bot-message' : 'user-message';
        msgEl.innerHTML = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        chatEl.appendChild(msgEl);
        chatEl.scrollTop = chatEl.scrollHeight;
    }

    async function processarComando(esporte) {
        const chatUI = UIElements.chats[esporte];
        const comando = chatUI.input.value.trim();
        if (comando === '') return;
        appendMessage(esporte, 'user', comando);
        chatUI.input.value = '';

        let state = chatStates[esporte];

        if (state === 'initial' && comando.toLowerCase().includes('quero apostar')) {
            appendMessage(esporte, 'bot', "Excelente! Qual jogo você quer analisar? Use o formato **'Time A vs Time B'**.");
            chatStates[esporte] = 'waiting_game';
        } else if (state === 'waiting_game') {
            const times = comando.split(/ vs | x /i);
            if (times.length !== 2) {
                appendMessage(esporte, 'bot', "Formato inválido. Por favor, use **'Time A vs Time B'**.");
                return;
            }
            jogoParaAnalisar = { time_casa: times[0].trim(), time_fora: times[1].trim(), esporte: esporte };
            appendMessage(esporte, 'bot', `Entendido. E qual o campeonato/liga para este jogo?`);
            chatStates[esporte] = 'waiting_league';
        } else if (state === 'waiting_league') {
            jogoParaAnalisar.campeonato = comando;
            appendMessage(esporte, 'bot', `Ok. Buscando e analisando dados para **${jogoParaAnalisar.time_casa} vs ${jogoParaAnalisar.time_fora}**. Aguarde...`);
            
            try {
                const response = await fetch('/analisar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(jogoParaAnalisar),
                });
                if (!response.ok) throw new Error('O servidor retornou um erro.');
                const analise = await response.json();
                
                appendMessage(esporte, 'bot', '--- 📊 **ANÁLISE CONCLUÍDA** 📊 ---');
                if (analise.melhor_aposta) {
                    const best = analise.melhor_aposta;
                    appendMessage(esporte, 'bot', `**MELHOR ENTRADA IDENTIFICADA:**`);
                    appendMessage(esporte, 'bot', `<strong>Mercado:</strong> ${best.mercado}  
<strong>Entrada:</strong> ${best.entrada}  
<strong>Odd Estimada:</strong> ${best.odd}  
<strong>Confiança:</strong> ${best.confianca || 'N/A'}`);
                    appendMessage(esporte, 'bot', `<strong>Justificativa:</strong> <em>${best.justificativa}</em>`);
                }
                if (analise.outras_opcoes && analise.outras_opcoes.length > 0) {
                    appendMessage(esporte, 'bot', `--- 💡 **OUTRAS OPÇÕES DE VALOR** ---`);
                    analise.outras_opcoes.forEach(opt => {
                         appendMessage(esporte, 'bot', `<strong>Mercado:</strong> ${opt.mercado}  
<strong>Entrada:</strong> ${opt.entrada} (${opt.odd})`);
                    });
                }
            } catch (error) {
                console.error('Erro ao contatar a API:', error);
                appendMessage(esporte, 'bot', 'Desculpe, não consegui conectar ao servidor de análise.');
            } finally {
                chatStates[esporte] = 'initial';
                jogoParaAnalisar = {};
                appendMessage(esporte, 'bot', "Análise finalizada. Digite **'Quero Apostar'** para um novo jogo.");
            }
        } else {
            appendMessage(esporte, 'bot', "Comando não reconhecido. Digite **'Quero Apostar'** para iniciar.");
        }
    }

    // =========================================================
    // LÓGICA DE GESTÃO DE BANCA E UI
    // =========================================================
    function getTodayDate() { return new Date().toLocaleDateString('pt-BR'); }
    function salvarDados() {
        const dados = { apostas: apostasRegistradas, config: { bancaInicial: BANCA_INICIAL, metaMinima: META_MINIMA, stakeMaxima: TETO_MAXIMO_STAKE } };
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
        if (confirm(`ATENÇÃO: Resetar todos os dados?`)) {
            apostasRegistradas = [];
            salvarDados();
            recalcularBanca();
            atualizarUI();
            alert("Dados resetados!");
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
        if (stake > TETO_MAXIMO_STAKE && !confirm(`Stake maior que o teto. Continuar?`)) return;
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
            if (apota.resultado === 'pending') {
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
            UIElements.alertaRisco.textContent = '⚠️ LIMITE DIÁRIO ATINGIDO!';
        } else if (resultadosDoDia.slice(-LIMITE_RED_SEQUENCIAL).every(r => r === 'red') && resultadosDoDia.length >= LIMITE_RED_SEQUENCIAL) {
            UIElements.alertaRisco.className = 'alerta ativo alerta-stop';
            UIElements.alertaRisco.textContent = `🚨 STOP LOSS! ${LIMITE_RED_SEQUENCIAL} REDs seguidos.`;
        } else if (bancaAtual >= META_MINIMA) {
            UIElements.alertaRisco.className = 'alerta ativo alerta-limite';
            UIElements.alertaRisco.textContent = `🏆 PARABÉNS! META ATINGIDA!`;
        }
    }
    
    function openTab(tabId) {
        esporteAtivo = tabId;
        
        document.body.classList.remove('theme-futebol', 'theme-nfl', 'theme-nba', 'theme-gestao');
        document.body.classList.add(`theme-${tabId}`);
        
        const todasAbas = [UIElements.futebolTab, UIElements.nflTab, UIElements.nbaTab, UIElements.gestaoTab];
        const todosBotoes = [UIElements.btnFutebolTab, UIElements.btnNflTab, UIElements.btnNbaTab, UIElements.btnGestaoTab];
        
        todasAbas.forEach(tab => tab.style.display = 'none');
        todosBotoes.forEach(btn => btn.classList.remove('active'));

        if (tabId === 'futebol') {
            UIElements.futebolTab.style.display = 'block';
            UIElements.btnFutebolTab.classList.add('active');
        } else if (tabId === 'nfl') {
            UIElements.nflTab.style.display = 'block';
            UIElements.btnNflTab.classList.add('active');
        } else if (tabId === 'nba') {
            UIElements.nbaTab.style.display = 'block';
            UIElements.btnNbaTab.classList.add('active');
        } else if (tabId === 'gestao') {
            UIElements.gestaoTab.style.display = 'block';
            UIElements.btnGestaoTab.classList.add('active');
        }
    }

    // =========================================================
    // INICIALIZAÇÃO E EVENTOS
    // =========================================================
    function init() {
        // Navegação por Abas - CORRIGIDO
        UIElements.btnFutebolTab.addEventListener('click', () => openTab('futebol'));
        UIElements.btnNflTab.addEventListener('click', () => openTab('nfl'));
        UIElements.btnNbaTab.addEventListener('click', () => openTab('nba'));
        UIElements.btnGestaoTab.addEventListener('click', () => openTab('gestao'));

        // Eventos de Chat para cada esporte
        Object.keys(UIElements.chats).forEach(esporte => {
            const chatUI = UIElements.chats[esporte];
            chatUI.btn.addEventListener('click', () => processarComando(esporte));
            chatUI.input.addEventListener('keyup', (e) => {
                if (e.key === 'Enter') processarComando(esporte);
            });
        });

        // Eventos da Gestão de Banca
        UIElements.btnConfigurarBanca.addEventListener('click', configurarBanca);
        UIElements.btnRegistrarAposta.addEventListener('click', adicionarAposta);
        UIElements.btnReset.addEventListener('click', resetarDados);

        // Carregar dados e definir estado inicial
        carregarDados();
        openTab('futebol');
    }

    init();
});

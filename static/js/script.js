// =================================================================
// ARQUIVO script.js - VERSÃO FINAL COM INDENTAÇÃO CORRIGIDA
// =================================================================
document.addEventListener('DOMContentLoaded', function() {

    // 1. MAPEAMENTO DOS ELEMENTOS DA UI
    const UIElements = {
        tabs: document.querySelectorAll('.tab-button'),
        tabContents: document.querySelectorAll('.tab-content'),
        chats: {
            futebol: {
                chatContainer: document.getElementById('chat-futebol'),
                input: document.getElementById('chat-input-futebol'),
                sendButton: document.getElementById('send-button-futebol')
            },
            nfl: {
                chatContainer: document.getElementById('chat-nfl'),
                input: document.getElementById('chat-input-nfl'),
                sendButton: document.getElementById('send-button-nfl')
            },
            nba: {
                chatContainer: document.getElementById('chat-nba'),
                input: document.getElementById('chat-input-nba'),
                sendButton: document.getElementById('send-button-nba')
            }
        },
        bancaAtualEl: document.getElementById('banca-atual'),
        stakeMaxEl: document.getElementById('stake-max'),
        apostasHojeEl: document.getElementById('apostas-hoje'),
        alertaRiscoEl: document.getElementById('alerta-risco'),
        tabelaBody: document.querySelector('#tabela-apostas tbody'),
        dataHojeEl: document.getElementById('data-hoje'),
        configBancaInicialEl: document.getElementById('config-banca-inicial'),
        configMetaMinimaEl: document.getElementById('config-meta-minima'),
        configStakeMaxEl: document.getElementById('config-stake-max'),
        btnConfig: document.querySelector('.config-form button'),
        btnAddAposta: document.querySelector('.input-form button'),
        btnReset: document.getElementById('reset-button')
    };

    // 2. ESTADO DA APLICAÇÃO
    let bancaAtual = 0.00;
    let apostasHoje = 0;
    let resultadosDoDia = [];
    let apostasRegistradas = [];
    let BANCA_INICIAL = 30.00;
    let META_MINIMA = 200.00;
    let TETO_MAXIMO_STAKE = 3.00;
    const LIMITE_APOSTAS_DIARIO = 10;
    const LIMITE_RED_SEQUENCIAL = 3;
    const chatStates = {
        futebol: { state: 'initial', timeA: {}, timeB: {} },
        nfl: { state: 'initial', timeA: {}, timeB: {} },
        nba: { state: 'initial', timeA: {}, timeB: {} }
    };

    // 3. FUNÇÕES DA APLICAÇÃO

    function getTodayDate() {
        return new Date().toLocaleDateString('pt-BR');
    }

    function salvarDados() {
        const dados = {
            banca: bancaAtual,
            apostas: apostasRegistradas,
            apostasHojeCount: apostasHoje,
            config: { bancaInicial: BANCA_INICIAL, metaMinima: META_MINIMA, stakeMaxima: TETO_MAXIMO_STAKE }
        };
        localStorage.setItem('gestaoBancaData', JSON.stringify(dados));
    }

    function carregarDados() {
        const dadosSalvos = localStorage.getItem('gestaoBancaData');
        if (dadosSalvos) {
            const dados = JSON.parse(dadosSalvos);
            bancaAtual = dados.banca || 0;
            apostasRegistradas = dados.apostas || [];
            apostasHoje = dados.apostasHojeCount || 0;
            BANCA_INICIAL = dados.config.bancaInicial || 30.00;
            META_MINIMA = dados.config.metaMinima || 200.00;
            TETO_MAXIMO_STAKE = dados.config.stakeMaxima || 3.00;
        }
        UIElements.configBancaInicialEl.value = BANCA_INICIAL.toFixed(2);
        UIElements.configMetaMinimaEl.value = META_MINIMA.toFixed(2);
        UIElements.configStakeMaxEl.value = TETO_MAXIMO_STAKE.toFixed(2);
        if (apostasRegistradas.length === 0) {
            bancaAtual = BANCA_INICIAL;
        } else {
            recalcularBanca();
        }
    }

    function openTab(tabName) {
        document.body.className = `theme-${tabName}`;
        UIElements.tabContents.forEach(content => content.classList.remove('active'));
        UIElements.tabs.forEach(tab => tab.classList.remove('active'));
        const activeContent = document.getElementById(`${tabName}-tab`);
        const activeTab = document.querySelector(`.tab-button[onclick*="'${tabName}'"]`);
        if (activeContent) activeContent.classList.add('active');
        if (activeTab) activeTab.classList.add('active');
    }

    function appendMessageToChat(chatContainer, sender, message) {
        const msgEl = document.createElement('p');
        msgEl.classList.add(sender === 'bot' ? 'bot-message' : 'user-message');
        msgEl.innerHTML = message;
        chatContainer.appendChild(msgEl);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    async function carregarCampeonatosDisponiveis() {
        try {
            const url = `${window.location.origin}/campeonatos`;
            const response = await fetch(url);
            if (!response.ok) throw new Error('Resposta do servidor não foi OK');
            const campeonatos = await response.json();
            const listaFormatada = campeonatos.map(c => `• ${c.charAt(0).toUpperCase() + c.slice(1)}`).join('  ');
            const mensagem = `Para análise com dados reais, use um dos seguintes campeonatos:  
  
${listaFormatada}`;
            const chatFutebol = UIElements.chats.futebol.chatContainer;
            const msgEl = document.createElement('p');
            msgEl.classList.add('bot-message', 'info-message');
            msgEl.innerHTML = mensagem;
            chatFutebol.appendChild(msgEl);
            chatFutebol.scrollTop = chatFutebol.scrollHeight;
        } catch (error) {
            console.error("Erro ao carregar campeonatos:", error);
            appendMessageToChat(UIElements.chats.futebol.chatContainer, 'bot', 'Não foi possível carregar a lista de campeonatos disponíveis.');
        }
    }

    async function processarComando(esporte) {
        const chatUI = UIElements.chats[esporte];
        const chatState = chatStates[esporte];
        const comando = chatUI.input.value.trim();
        if (comando === '') return;
        appendMessageToChat(chatUI.chatContainer, 'user', comando);
        chatUI.input.value = '';

        if (chatState.state === 'initial' && comando.toLowerCase().includes('quero apostar')) {
            appendMessageToChat(chatUI.chatContainer, 'bot', "Excelente! Qual jogo (Time A vs Time B) você quer analisar?");
            chatState.state = 'waiting_game';
            return;
        }
        if (chatState.state === 'waiting_game') {
            const times = comando.split(' vs ');
            if (times.length !== 2) {
                appendMessageToChat(chatUI.chatContainer, 'bot', "Formato inválido. Use 'Time A vs Time B'.");
                return;
            }
            chatState.timeA.nome = times[0].trim();
            chatState.timeB.nome = times[1].trim();
            appendMessageToChat(chatUI.chatContainer, 'bot', `Entendido. E qual o campeonato?`);
            chatState.state = 'waiting_league';
            return;
        }
        if (chatState.state === 'waiting_league') {
            chatState.campeonato = comando;
            appendMessageToChat(chatUI.chatContainer, 'bot', `Ok, buscando análise para <strong>${chatState.timeA.nome} vs ${chatState.timeB.nome}</strong>...`);
            chatState.state = 'analyzing';
            
            try {
                const url = `${window.location.origin}/analisar`;
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        esporte: esporte,
                        time_casa: chatState.timeA.nome,
                        time_fora: chatState.timeB.nome,
                        campeonato: chatState.campeonato
                    })
                });
                const data = await response.json();
                if (data.erro) {
                    appendMessageToChat(chatUI.chatContainer, 'bot', `⚠️ Erro: ${data.erro}`);
                } else {
                    const { melhor_aposta, outras_opcoes } = data;
                    let analiseHTML = `<strong>🎯 Melhor Entrada:</strong>  

                        <strong>Mercado:</strong> ${melhor_aposta.mercado}  

                        <strong>Entrada:</strong> ${melhor_aposta.entrada}  

                        <strong>Confiança:</strong> ${melhor_aposta.confianca}  

                        <i>${melhor_aposta.justificativa}</i>  
  
`;
                    
                    if (outras_opcoes && outras_opcoes.length > 0) {
                        analiseHTML += `<strong>🔎 Outras Opções de Valor:</strong>  
`;
                        outras_opcoes.forEach(op => {
                            analiseHTML += `• <strong>${op.mercado}:</strong> ${op.entrada} (${op.confianca})  
`;
                        });
                    }
                    appendMessageToChat(chatUI.chatContainer, 'bot', analiseHTML);
                }
            } catch (error) {
                console.error("Erro na API:", error);
                appendMessageToChat(chatUI.chatContainer, 'bot', "Desculpe, não consegui conectar ao servidor de análise.");
            }
            
            appendMessageToChat(chatUI.chatContainer, 'bot', `Análise concluída. Digite "Quero Apostar" para um novo jogo.`);
            chatState.state = 'initial';
            return;
        }
        appendMessageToChat(chatUI.chatContainer, 'bot', 'Comando não reconhecido. Digite "Quero Apostar" para iniciar.');
    }

    function atualizarUI() {
        UIElements.bancaAtualEl.textContent = `R$ ${bancaAtual.toFixed(2)}`;
        UIElements.stakeMaxEl.textContent = `R$ ${TETO_MAXIMO_STAKE.toFixed(2)}`;
        UIElements.apostasHojeEl.textContent = `${apostasHoje}/${LIMITE_APOSTAS_DIARIO}`;
        UIElements.dataHojeEl.textContent = getTodayDate();
        renderizarTabela();
        verificarAlertas();
    }

    function verificarAlertas() {
        UIElements.alertaRiscoEl.className = 'alerta';
        UIElements.alertaRiscoEl.textContent = '';
        if (apostasHoje >= LIMITE_APOSTAS_DIARIO) {
            UIElements.alertaRiscoEl.classList.add('ativo', 'alerta-limite');
            UIElements.alertaRiscoEl.textContent = '⚠️ LIMITE DIÁRIO ATINGIDO!';
        }
        let redSeguidos = 0;
        for (let i = resultadosDoDia.length - 1; i >= 0; i--) {
            if (resultadosDoDia[i] === 'red') redSeguidos++;
            else if (resultadosDoDia[i] === 'win') break;
        }
        if (redSeguidos >= LIMITE_RED_SEQUENCIAL) {
            UIElements.alertaRiscoEl.classList.add('ativo', 'alerta-stop');
            UIElements.alertaRiscoEl.textContent = `🚨 STOP LOSS! ${redSeguidos} REDs seguidos.`;
        }
        if (bancaAtual >= META_MINIMA) {
            UIElements.alertaRiscoEl.classList.add('ativo', 'alerta-limite');
            UIElements.alertaRiscoEl.textContent = `🏆 PARABÉNS! META ATINGIDA!`;
        }
    }

    function adicionarAposta() {
        const stake = parseFloat(document.getElementById('input-stake').value);
        const odd = parseFloat(document.getElementById('input-odd').value);
        const resultado = document.getElementById('input-resultado').value;
        const acrescimo = parseFloat(document.getElementById('input-acrescimo').value) || 0.00;
        if (!stake || !odd || !resultado) {
            alert("Preencha Stake, Odd e Resultado.");
            return;
        }
        if (stake > TETO_MAXIMO_STAKE) {
            alert(`A Stake Máxima permitida é de R$ ${TETO_MAXIMO_STAKE.toFixed(2)}.`);
            return;
        }
        if (stake <= 0) {
            alert("A Stake deve ser um valor positivo.");
            return;
        }
        let ganhoPerdaCalculado;
        if (resultado === 'win') ganhoPerdaCalculado = stake * (odd - 1) + acrescimo;
        else if (resultado === 'red') ganhoPerdaCalculado = -stake;
        else ganhoPerdaCalculado = 0;
        const novaAposta = {
            id: Date.now(),
            data: getTodayDate(),
            stake: stake,
            odd: odd,
            resultado: resultado,
            acrescimo: acrescimo,
            ganhoPerda: ganhoPerdaCalculado
        };
        apostasRegistradas.push(novaAposta);
        apostasHoje++;
        if (novaAposta.resultado !== 'pending') {
            bancaAtual += novaAposta.ganhoPerda;
            resultadosDoDia.push(novaAposta.resultado);
        }
        salvarDados();
        atualizarUI();
        document.getElementById('input-stake').value = '';
        document.getElementById('input-odd').value = '';
        document.getElementById('input-resultado').value = '';
        document.getElementById('input-acrescimo').value = '0.00';
    }

    function renderizarTabela() {
        UIElements.tabelaBody.innerHTML = '';
        let bancaExibicao = BANCA_INICIAL;
        apostasRegistradas.forEach((aposta, index) => {
            const newRow = UIElements.tabelaBody.insertRow();
            let ganhoPerdaDisplay = aposta.ganhoPerda.toFixed(2);
            let bancaFinalDisplay;
            if (aposta.resultado !== 'pending') {
                bancaExibicao += aposta.ganhoPerda;
                bancaFinalDisplay = bancaExibicao.toFixed(2);
            } else {
                bancaFinalDisplay = 'PENDENTE';
            }
            const labels = ["Data", "#", "Stake (R$)", "Odd", "Resultado", "Ganho/Perda", "Acréscimo", "Banca Final", "Ação"];
            const values = [aposta.data, index + 1, aposta.stake.toFixed(2), aposta.odd.toFixed(2), aposta.resultado.toUpperCase(), (aposta.resultado === 'pending' ? '---' : ganhoPerdaDisplay), aposta.acrescimo.toFixed(2), bancaFinalDisplay, ''];
            values.forEach((value, i) => {
                let cell = newRow.insertCell(i);
                cell.setAttribute('data-label', labels[i]);
                cell.textContent = value;
            });
            newRow.querySelector('td:nth-child(5)').classList.add(aposta.resultado);
            if (aposta.resultado === 'pending') {
                const actionCell = newRow.cells[8];
                actionCell.setAttribute('data-label', 'Ação');
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

    function resolverAposta(apostaId, novoResultado) {
        const apostaIndex = apostasRegistradas.findIndex(a => a.id === apostaId);
        if (apostaIndex === -1) return;
        const aposta = apostasRegistradas[apostaIndex];
        if (aposta.resultado !== 'pending') return;
        let ganho = 0;
        if (novoResultado === 'win') ganho = aposta.stake * (aposta.odd - 1) + aposta.acrescimo;
        else ganho = -aposta.stake;
        aposta.resultado = novoResultado;
        aposta.ganhoPerda = ganho;
        recalcularBanca();
        salvarDados();
        atualizarUI();
    }

    function recalcularBanca() {
        let tempBanca = BANCA_INICIAL;
        resultadosDoDia = [];
        apostasRegistradas.forEach(aposta => {
            if (aposta.resultado !== 'pending') {
                tempBanca += aposta.ganhoPerda;
                resultadosDoDia.push(aposta.resultado);
            }
        });
        bancaAtual = tempBanca;
    }

    function configurarBanca() {
        const novaBancaInicial = parseFloat(UIElements.configBancaInicialEl.value);
        const novaMetaMinima = parseFloat(UIElements.configMetaMinimaEl.value);
        const novaStakeMax = parseFloat(UIElements.configStakeMaxEl.value);
        if (isNaN(novaBancaInicial) || isNaN(novaStakeMax) || isNaN(novaMetaMinima) || novaBancaInicial <= 0) {
            alert("Preencha as configurações com valores válidos.");
            return;
        }
        BANCA_INICIAL = novaBancaInicial;
        META_MINIMA = novaMetaMinima;
        TETO_MAXIMO_STAKE = novaStakeMax;
        if (apostasRegistradas.length === 0) {
            bancaAtual = BANCA_INICIAL;
        }
        salvarDados();
        atualizarUI();
        alert("Configurações aplicadas!");
    }

    function resetarDados() {
        if (confirm(`ATENÇÃO: Deseja RESETAR todos os dados? A banca voltará para R$ ${BANCA_INICIAL.toFixed(2)}.`)) {
            bancaAtual = BANCA_INICIAL;
            apostasRegistradas = [];
            apostasHoje = 0;
            resultadosDoDia = [];
            salvarDados();
            atualizarUI();
            alert("Dados resetados com sucesso!");
        }
    }

    // 4. INICIALIZAÇÃO DA APLICAÇÃO
    function init() {
        carregarDados();
        atualizarUI();
        openTab('futebol');

        UIElements.tabs.forEach(tab => {
            const tabName = tab.getAttribute('onclick').match(/'([^']+)'/)[1];
            tab.addEventListener('click', () => openTab(tabName));
        });

        Object.keys(UIElements.chats).forEach(esporte => {
            const chatUI = UIElements.chats[esporte];
            chatUI.sendButton.addEventListener('click', () => processarComando(esporte));
            chatUI.input.addEventListener('keyup', (event) => {
                if (event.key === 'Enter') processarComando(esporte);
            });
        });

        UIElements.btnConfig.addEventListener('click', configurarBanca);
        UIElements.btnAddAposta.addEventListener('click', adicionarAposta);
        UIElements.btnReset.addEventListener('click', resetarDados);

        carregarCampeonatosDisponiveis();
    }

    init();
});

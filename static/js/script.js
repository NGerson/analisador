// Espera o documento HTML ser completamente carregado
document.addEventListener('DOMContentLoaded', () => {

    // --- GERENCIAMENTO DAS ABAS ---
    const tabs = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove a classe 'active' de todas as abas e conteúdos
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // Adiciona a classe 'active' na aba clicada e no seu conteúdo correspondente
            tab.classList.add('active');
            const targetTabContent = document.getElementById(tab.dataset.tab + '-tab');
            if (targetTabContent) {
                targetTabContent.classList.add('active');
            }
        });
    });

    // Ativa a primeira aba por padrão
    if (tabs.length > 0) {
        tabs[0].click();
    }

    // --- LÓGICA DO CHAT DE ANÁLISE ---
    const sendButtons = {
        futebol: document.getElementById('send-button-futebol'),
        nfl: document.getElementById('send-button-nfl'),
        nba: document.getElementById('send-button-nba')
    };

    const chatInputs = {
        futebol: document.getElementById('chat-input-futebol'),
        nfl: document.getElementById('chat-input-nfl'),
        nba: document.getElementById('chat-input-nba')
    };

    // Adiciona o evento de clique para cada botão de "Enviar"
    for (const esporte in sendButtons) {
        if (sendButtons[esporte]) {
            sendButtons[esporte].addEventListener('click', () => {
                const userInput = chatInputs[esporte].value;
                if (userInput.trim() !== "") {
                    iniciarAnalise(esporte, userInput);
                }
            });

            // Permite enviar com a tecla Enter
            chatInputs[esporte].addEventListener('keypress', (event) => {
                if (event.key === 'Enter') {
                    sendButtons[esporte].click();
                }
            });
        }
    }
    
    // Função para adicionar mensagens ao chat
    function appendMessage(esporte, sender, message) {
        const chatContainer = document.getElementById(`chat-${esporte}`);
        if (chatContainer) {
            const messageElement = document.createElement('p');
            messageElement.className = `${sender}-message`;
            messageElement.innerHTML = message; // Usamos innerHTML para renderizar o HTML
            chatContainer.appendChild(messageElement);
            chatContainer.scrollTop = chatContainer.scrollHeight; // Rola para a última mensagem
        }
    }

    // Função para iniciar a análise (comunicação com o backend)
    async function iniciarAnalise(esporte, mensagem) {
        appendMessage(esporte, 'user', mensagem);
        chatInputs[esporte].value = ''; // Limpa o input

        appendMessage(esporte, 'bot', 'Analisando, por favor aguarde...');

        try {
            const response = await fetch('/analisar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ esporte: esporte, mensagem: mensagem }),
            });

            if (!response.ok) {
                throw new Error(`Erro de rede: ${response.statusText}`);
            }

            const data = await response.json();
            exibirResultadoAnalise(esporte, data);

        } catch (error) {
            appendMessage(esporte, 'bot', `⚠️ Erro na comunicação com o servidor: ${error.message}`);
        }
    }

    // Função que você me enviou (colocada aqui dentro do escopo)
    function exibirResultadoAnalise(esporte, data) {
        if (data.erro) {
            appendMessage(esporte, 'bot', `⚠️ Erro: ${data.erro}`);
            return;
        }

        const melhorAposta = data.melhor_aposta;
        let resultadoHTML = `<strong>🚀 Melhor Entrada:</strong> ${melhorAposta.mercado}: <strong>${melhorAposta.palpite}</strong> (Confiança: ${melhorAposta.confianca}%)  
<em>${melhorAposta.justificativa}</em>`;

        if (data.outras_opcoes && data.outras_opcoes.length > 0) {
            resultadoHTML += `  
  
<strong>🔎 Outras Opções de Valor:</strong>`;
            data.outras_opcoes.forEach(opcao => {
                resultadoHTML += `  
• ${opcao.mercado}: <strong>${opcao.palpite}</strong> (${opcao.confianca}%)`;
            });
        }

        appendMessage(esporte, 'bot', resultadoHTML);
    }

    // Aqui você adicionaria a lógica da aba "Gestão"
    // ...
});

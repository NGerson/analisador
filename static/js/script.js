document.addEventListener('DOMContentLoaded', () => {

    // --- GERENCIAMENTO DAS ABAS ---
    const tabs = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            const targetTabContent = document.getElementById(tab.dataset.tab + '-tab');
            if (targetTabContent) {
                targetTabContent.classList.add('active');
            }
        });
    });

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

    for (const esporte in sendButtons) {
        if (sendButtons[esporte]) {
            sendButtons[esporte].addEventListener('click', () => {
                const userInput = chatInputs[esporte].value;
                if (userInput.trim() !== "") {
                    handleUserMessage(esporte, userInput);
                }
            });

            chatInputs[esporte].addEventListener('keypress', (event) => {
                if (event.key === 'Enter') {
                    sendButtons[esporte].click();
                }
            });
        }
    }
    
    function appendMessage(esporte, sender, message) {
        const chatContainer = document.getElementById(`chat-${esporte}`);
        if (chatContainer) {
            const messageElement = document.createElement('p');
            messageElement.className = `${sender}-message`;
            messageElement.innerHTML = message;
            chatContainer.appendChild(messageElement);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }

    async function handleUserMessage(esporte, mensagem) {
        appendMessage(esporte, 'user', mensagem);
        chatInputs[esporte].value = '';

        // Mostra "Analisando..." apenas se não for o início da conversa
        if (mensagem.toLowerCase().indexOf('quero apostar') === -1) {
             appendMessage(esporte, 'bot', 'Analisando, por favor aguarde...');
        }

        try {
            const response = await fetch('/analisar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ esporte: esporte, mensagem: mensagem }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.erro || `Erro de rede: ${response.statusText}`);
            }

            const data = await response.json();

            // Remove a mensagem "Analisando..." se ela existir
            const analyzingMessage = Array.from(document.querySelectorAll(`#chat-${esporte} .bot-message`)).pop();
            if (analyzingMessage && analyzingMessage.textContent.includes('Analisando')) {
                analyzingMessage.remove();
            }

            // Verifica o tipo de resposta do backend
            if (data.bot_response) {
                // É uma resposta de texto simples (ex: pedido de mais informações)
                appendMessage(esporte, 'bot', data.bot_response);
            } else if (data.melhor_aposta) {
                // É o resultado final da análise
                exibirResultadoAnalise(esporte, data);
            } else if (data.erro) {
                // É uma mensagem de erro
                appendMessage(esporte, 'bot', `⚠️ Erro: ${data.erro}`);
            }

        } catch (error) {
            appendMessage(esporte, 'bot', `⚠️ Erro na comunicação: ${error.message}`);
        }
    }

    function exibirResultadoAnalise(esporte, data) {
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
});

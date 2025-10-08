function exibirResultadoAnalise(esporte, data) {
    const chat = UIElements.chats[esporte];
    
    if (data.erro) {
        appendMessage(esporte, 'bot', `⚠️ Erro: ${data.erro}`);
        return;
    }

    // CORREÇÃO APLICADA AQUI: Usando 'palpite' em vez de 'entrada'
    const melhorAposta = data.melhor_aposta;
    let resultadoHTML = `<strong>🚀 Melhor Entrada:</strong> ${melhorAposta.mercado}: <strong>${melhorAposta.palpite}</strong> (Confiança: ${melhorAposta.confianca}%)  
<em>${melhorAposta.justificativa}</em>`;

    if (data.outras_opcoes && data.outras_opcoes.length > 0) {
        resultadoHTML += `  
  
<strong>🔎 Outras Opções de Valor:</strong>`;
        data.outras_opcoes.forEach(opcao => {
            // CORREÇÃO APLICADA AQUI: Usando 'palpite' em vez de 'entrada'
            resultadoHTML += `  
• ${opcao.mercado}: <strong>${opcao.palpite}</strong> (${opcao.confianca}%)`;
        });
    }

    appendMessage(esporte, 'bot', resultadoHTML);
}

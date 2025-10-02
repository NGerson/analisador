# Importe 'render_template' e 'send_from_directory'
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import random
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# --- ROTA PARA SERVIR A PÁGINA PRINCIPAL (index.html) ---
@app.route('/')
def home():
    # Flask vai procurar por 'index.html' na pasta 'templates'
    return render_template('index.html')

# --- ROTA PARA SERVIR ARQUIVOS ESTÁTICOS (CSS, JS) ---
# Esta rota é uma garantia, embora o Flask geralmente faça isso automaticamente.
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


# --- SUA ROTA DA API (sem alterações) ---
@app.route('/analisar', methods=['POST'])
def analisar_jogo():
    dados = request.get_json()
    time_casa = dados.get('time_casa')
    time_fora = dados.get('time_fora')
    campeonato = dados.get('campeonato')

    if not all([time_casa, time_fora, campeonato]):
        return jsonify({"erro": "Dados incompletos."}), 400

    resultado_analise = buscar_e_analisar_dados(time_casa, time_fora, campeonato)
    return jsonify(resultado_analise)


# Dentro do servidor.py, substitua a função existente por esta:
     # COLE ESTE NOVO BLOCO NO LUGAR DO ANTIGO
def buscar_e_analisar_dados(time_casa, time_fora, campeonato):
    """
    Função de análise para Futebol, agora com cálculo de confiança.
    """
    print(f"Recebido pedido para analisar FUTEBOL: {time_casa} vs {time_fora} no {campeonato}")

    # Simulação de notas de ataque e defesa
    ataque_casa = round(random.uniform(2.5, 5.0), 1)
    defesa_casa = round(random.uniform(2.5, 5.0), 1)
    ataque_fora = round(random.uniform(2.0, 4.5), 1)
    defesa_fora = round(random.uniform(2.0, 4.8), 1)

    poder_ataque_casa = ataque_casa - defesa_fora
    poder_ataque_fora = ataque_fora - defesa_casa
    
    tips = []
    
    # --- LÓGICA DE CONFIANÇA ---
    def calcular_confianca(diferenca_poder):
        confianca_base = 65  # Confiança mínima para uma aposta sugerida
        bonus = abs(diferenca_poder) * 10
        confianca_final = min(confianca_base + bonus, 95) # Limita a confiança máxima
        return int(confianca_final)

    # 1. Análise de Gols
    diferenca_gols = (poder_ataque_casa + poder_ataque_fora) / 2
    confianca_gols = calcular_confianca(diferenca_gols)
    
    if poder_ataque_casa > 1.5 and poder_ataque_fora > 1.0:
        tips.append({
            "mercado": "Gols (Over/Under)",
            "entrada": "Mais de 2.5 gols (Over 2.5)",
            "odd": f"~{round(random.uniform(1.75, 2.10), 2)}",
            "justificativa": "Ataques fortes contra defesas vulneráveis indicam um jogo aberto.",
            "confianca": f"{confianca_gols}%"
        })
    elif poder_ataque_casa < 0.5 and poder_ataque_fora < 0.5:
        tips.append({
            "mercado": "Gols (Over/Under)",
            "entrada": "Menos de 2.5 gols (Under 2.5)",
            "odd": f"~{round(random.uniform(1.70, 1.95), 2)}",
            "justificativa": "Jogo tende a ser fechado, com duas defesas fortes que devem neutralizar os ataques.",
            "confianca": f"{confianca_gols}%"
        })
    else:
        # A confiança para "Ambas Marcam" pode ser baseada em uma lógica diferente,
        # aqui vamos usar a média como exemplo
        confianca_ambas = calcular_confianca((ataque_casa + ataque_fora) / 2 - 3.5)
        tips.append({
            "mercado": "Ambas Marcam",
            "entrada": "Sim",
            "odd": f"~{round(random.uniform(1.80, 2.20), 2)}",
            "justificativa": "Equilíbrio entre os ataques e defesas, com boas chances de ambos os times marcarem.",
            "confianca": f"{confianca_ambas}%"
        })

    # 2. Análise de Vencedor
    diferenca_vencedor = poder_ataque_casa - poder_ataque_fora
    confianca_vencedor = calcular_confianca(diferenca_vencedor)

    if diferenca_vencedor > 1.2: # Limiar um pouco menor para incluir mais cenários
         tips.append({
            "mercado": "Resultado de Valor",
            "entrada": f"Handicap Asiático {time_casa} -0.5",
            "odd": f"~{round(random.uniform(1.90, 2.30), 2)}",
            "justificativa": f"A análise mostra uma superioridade técnica e tática para o {time_casa}, tornando a vitória uma aposta de valor.",
            "confianca": f"{confianca_vencedor}%"
        })

    if not tips:
        return {"erro": "Não foi possível gerar uma análise para este jogo."}

    # Ordena as tips pela confiança (da maior para a menor) para que a melhor sempre venha primeiro
    tips.sort(key=lambda x: int(x.get('confianca', '0').replace('%', '')), reverse=True)

    return {
        "melhor_aposta": tips[0],
        "outras_opcoes": tips[1:]
    }

    
    # --- NOVA LÓGICA DE CONFIANÇA ---
    def calcular_confianca(diferenca_poder):
        # Converte a "diferença de poder" em uma porcentagem de confiança
        confianca_base = 60  # Confiança mínima para uma aposta
        bonus = abs(diferenca_poder) * 10
        confianca_final = min(confianca_base + bonus, 95) # Limita a confiança máxima a 95%
        return int(confianca_final)

    # 1. Análise de Gols
    diferenca_gols = (poder_ataque_casa + poder_ataque_fora) / 2
    confianca_gols = calcular_confianca(diferenca_gols)
    
    if poder_ataque_casa > 1.5 and poder_ataque_fora > 1.0:
        tips.append({
            "mercado": "Gols (Over/Under)",
            "entrada": "Mais de 2.5 gols (Over 2.5)",
            "odd": f"~{round(random.uniform(1.75, 2.10), 2)}",
            "justificativa": "Ataques fortes contra defesas vulneráveis indicam um jogo aberto.",
            "confianca": f"{confianca_gols}%" # <-- CAMPO ADICIONADO
        })
    # ... (outras lógicas de gols)

    # Adicione o campo "confianca" nas outras tips também, usando a mesma lógica.
    # Por exemplo, para a aposta de vencedor:
    diferenca_vencedor = poder_ataque_casa - poder_ataque_fora
    confianca_vencedor = calcular_confianca(diferenca_vencedor)

    if diferenca_vencedor > 1.5:
         tips.append({
            "mercado": "Resultado de Valor",
            "entrada": f"Handicap Asiático {time_casa} -0.5",
            "odd": f"~{round(random.uniform(1.90, 2.30), 2)}",
            "justificativa": f"Superioridade técnica e tática significativa para o {time_casa}.",
            "confianca": f"{confianca_vencedor}%" # <-- CAMPO ADICIONADO
        })

    # ... (Resto da função)

    # Certifique-se de que a função de retorno inclua o novo campo.
    # O código javascript já está preparado para exibir qualquer campo que a API retornar.
    if not tips:
        return {"erro": "Não foi possível gerar uma análise para este jogo."}

    # Ordena as tips pela confiança (da maior para a menor)
    tips.sort(key=lambda x: int(x.get('confianca', '0').replace('%', '')), reverse=True)

    return {
        "melhor_aposta": tips[0],
        "outras_opcoes": tips[1:]
    }


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False) # debug=False é melhor para produção

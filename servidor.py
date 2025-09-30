from flask import Flask, request, jsonify
from flask_cors import CORS
import random

# Inicializa o servidor Flask
app = Flask(__name__)
# Permite que o frontend (rodando em outra porta) se comunique com este servidor
CORS(app)

def buscar_e_analisar_dados(time_casa, time_fora, campeonato):
    """
    FUNÇÃO SIMULADA DE ANÁLISE
    No mundo real, esta função usaria 'requests' e 'BeautifulSoup' para
    buscar dados reais de sites de estatísticas.
    
    Para este exemplo, vamos gerar dados aleatórios realistas para simular a análise.
    """
    print(f"Recebido pedido para analisar: {time_casa} vs {time_fora} no {campeonato}")

    # Simulação de notas de ataque e defesa (de 2.0 a 5.0)
    ataque_casa = round(random.uniform(2.5, 5.0), 1)
    defesa_casa = round(random.uniform(2.5, 5.0), 1)
    ataque_fora = round(random.uniform(2.0, 4.5), 1)
    defesa_fora = round(random.uniform(2.0, 4.8), 1)

    # Lógica de análise para gerar tips
    poder_ataque_casa = ataque_casa - defesa_fora
    poder_ataque_fora = ataque_fora - defesa_casa
    
    tips = []

    # 1. Análise de Gols
    if poder_ataque_casa > 1.5 and poder_ataque_fora > 1.0:
        tips.append({
            "mercado": "Gols (Over/Under)",
            "entrada": "Mais de 2.5 gols (Over 2.5)",
            "odd": f"~{round(random.uniform(1.75, 2.10), 2)}",
            "justificativa": "Ambos os times têm ataques superiores às defesas adversárias, indicando um jogo aberto e com alta probabilidade de gols."
        })
    elif poder_ataque_casa < 0.5 and poder_ataque_fora < 0.5:
        tips.append({
            "mercado": "Gols (Over/Under)",
            "entrada": "Menos de 2.5 gols (Under 2.5)",
            "odd": f"~{round(random.uniform(1.70, 1.95), 2)}",
            "justificativa": "Jogo tende a ser fechado, com duas defesas fortes que devem neutralizar os ataques."
        })
    else:
        tips.append({
            "mercado": "Ambas Marcam",
            "entrada": "Sim",
            "odd": f"~{round(random.uniform(1.80, 2.20), 2)}",
            "justificativa": "Equilíbrio entre os ataques e defesas, com boas chances de ambos os times marcarem."
        })

    # 2. Análise de Escanteios (baseada no poder de ataque)
    if ataque_casa > 4.0 and ataque_fora > 3.5:
        tips.append({
            "mercado": "Escanteios",
            "entrada": "Mais de 9.5 escanteios",
            "odd": f"~{round(random.uniform(1.85, 2.05), 2)}",
            "justificativa": "Ambos os times são muito ofensivos e atacam pelas laterais, o que historicamente gera um alto número de escanteios."
        })

    # 3. Análise de Vencedor (a aposta de maior valor)
    if poder_ataque_casa - poder_ataque_fora > 1.5:
         tips.append({
            "mercado": "Resultado de Valor",
            "entrada": f"Handicap Asiático {time_casa} -0.5",
            "odd": f"~{round(random.uniform(1.90, 2.30), 2)}",
            "justificativa": f"A análise mostra uma superioridade técnica e tática significativa para o {time_casa}, tornando a vitória uma aposta de valor."
        })

    if not tips:
        return {"erro": "Não foi possível gerar uma análise para este jogo."}

    return {
        "melhor_aposta": tips[0],
        "outras_opcoes": tips[1:]
    }


# Define a rota da API. Ex: http://127.0.0.1:5000/analisar
@app.route('/analisar', methods=['POST'] )
def analisar_jogo():
    dados = request.get_json()
    time_casa = dados.get('time_casa')
    time_fora = dados.get('time_fora')
    campeonato = dados.get('campeonato')

    if not all([time_casa, time_fora, campeonato]):
        return jsonify({"erro": "Dados incompletos."}), 400

    resultado_analise = buscar_e_analisar_dados(time_casa, time_fora, campeonato)
    return jsonify(resultado_analise)

# Roda o servidor
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

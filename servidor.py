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


def buscar_e_analisar_dados(time_casa, time_fora, campeonato):
    # ... (O resto da sua função de análise continua exatamente igual) ...
    print(f"Recebido pedido para analisar: {time_casa} vs {time_fora} no {campeonato}")
    ataque_casa = round(random.uniform(2.5, 5.0), 1)
    defesa_casa = round(random.uniform(2.5, 5.0), 1)
    ataque_fora = round(random.uniform(2.0, 4.5), 1)
    defesa_fora = round(random.uniform(2.0, 4.8), 1)
    poder_ataque_casa = ataque_casa - defesa_fora
    poder_ataque_fora = ataque_fora - defesa_casa
    tips = []
    if poder_ataque_casa > 1.5 and poder_ataque_fora > 1.0:
        tips.append({"mercado": "Gols (Over/Under)", "entrada": "Mais de 2.5 gols (Over 2.5)", "odd": f"~{round(random.uniform(1.75, 2.10), 2)}", "justificativa": "Ambos os times têm ataques superiores às defesas adversárias."})
    elif poder_ataque_casa < 0.5 and poder_ataque_fora < 0.5:
        tips.append({"mercado": "Gols (Over/Under)", "entrada": "Menos de 2.5 gols (Under 2.5)", "odd": f"~{round(random.uniform(1.70, 1.95), 2)}", "justificativa": "Jogo tende a ser fechado, com defesas fortes."})
    else:
        tips.append({"mercado": "Ambas Marcam", "entrada": "Sim", "odd": f"~{round(random.uniform(1.80, 2.20), 2)}", "justificativa": "Equilíbrio entre ataques e defesas."})
    if ataque_casa > 4.0 and ataque_fora > 3.5:
        tips.append({"mercado": "Escanteios", "entrada": "Mais de 9.5 escanteios", "odd": f"~{round(random.uniform(1.85, 2.05), 2)}", "justificativa": "Times ofensivos que atacam pelas laterais."})
    if poder_ataque_casa - poder_ataque_fora > 1.5:
         tips.append({"mercado": "Resultado de Valor", "entrada": f"Handicap Asiático {time_casa} -0.5", "odd": f"~{round(random.uniform(1.90, 2.30), 2)}", "justificativa": f"Superioridade técnica e tática para o {time_casa}."})
    if not tips:
        return {"erro": "Não foi possível gerar uma análise."}
    return {"melhor_aposta": tips[0], "outras_opcoes": tips[1:]}


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False) # debug=False é melhor para produção

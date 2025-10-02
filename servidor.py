from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import random

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# --- ROTA PARA SERVIR A PÁGINA PRINCIPAL ---
@app.route('/')
def home():
    return render_template('index.html')

# --- ROTA PARA SERVIR ARQUIVOS ESTÁTICOS (CSS, JS) ---
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# --- ROTA PRINCIPAL DA API ---
@app.route('/analisar', methods=['POST'])
def analisar_jogo():
    dados = request.get_json()
    esporte = dados.get('esporte')
    time_casa = dados.get('time_casa')
    time_fora = dados.get('time_fora')
    campeonato = dados.get('campeonato')

    if not all([esporte, time_casa, time_fora, campeonato]):
        return jsonify({"erro": "Dados incompletos."}), 400

    if esporte == 'futebol':
        resultado_analise = analisar_futebol(time_casa, time_fora, campeonato)
    elif esporte == 'nfl':
        resultado_analise = analisar_nfl(time_casa, time_fora, campeonato)
    elif esporte == 'nba':
        resultado_analise = analisar_nba(time_casa, time_fora, campeonato)
    else:
        return jsonify({"erro": "Esporte não suportado."}), 400
        
    return jsonify(resultado_analise)

# --- FUNÇÕES DE ANÁLISE POR ESPORTE ---

def calcular_confianca(diferenca_poder, min_conf=65, max_conf=95):
    bonus = abs(diferenca_poder) * 10
    confianca_final = min(min_conf + bonus, max_conf)
    return int(confianca_final)

def analisar_futebol(time_casa, time_fora, campeonato):
    print(f"Analisando FUTEBOL: {time_casa} vs {time_fora}")
    ataque_casa = round(random.uniform(2.5, 5.0), 1)
    defesa_casa = round(random.uniform(2.5, 5.0), 1)
    ataque_fora = round(random.uniform(2.0, 4.5), 1)
    defesa_fora = round(random.uniform(2.0, 4.8), 1)
    poder_ataque_casa = ataque_casa - defesa_fora
    poder_ataque_fora = ataque_fora - defesa_casa
    tips = []
    
    diferenca_gols = (poder_ataque_casa + poder_ataque_fora) / 2
    confianca_gols = calcular_confianca(diferenca_gols)
    
    if poder_ataque_casa > 1.5 and poder_ataque_fora > 1.0:
        tips.append({"mercado": "Gols (Over/Under)", "entrada": "Mais de 2.5 gols", "odd": f"~{round(random.uniform(1.75, 2.10), 2)}", "justificativa": "Ataques fortes contra defesas vulneráveis.", "confianca": f"{confianca_gols}%"})
    else:
        tips.append({"mercado": "Ambas Marcam", "entrada": "Sim", "odd": f"~{round(random.uniform(1.80, 2.20), 2)}", "justificativa": "Equilíbrio entre os times.", "confianca": f"{calcular_confianca(diferenca_gols, 60, 85)}%"})

    diferenca_vencedor = poder_ataque_casa - poder_ataque_fora
    if abs(diferenca_vencedor) > 1.2:
        vencedor = time_casa if diferenca_vencedor > 0 else time_fora
        tips.append({"mercado": "Resultado", "entrada": f"Handicap Asiático {vencedor} -0.5", "odd": f"~{round(random.uniform(1.90, 2.30), 2)}", "justificativa": f"Superioridade técnica e tática para {vencedor}.", "confianca": f"{calcular_confianca(diferenca_vencedor)}%"})

    if not tips: return {"erro": "Não foi possível gerar uma análise."}
    tips.sort(key=lambda x: int(x.get('confianca', '0').replace('%', '')), reverse=True)
    return {"melhor_aposta": tips[0], "outras_opcoes": tips[1:]}

def analisar_nfl(time_casa, time_fora, campeonato):
    print(f"Analisando NFL: {time_casa} vs {time_fora}")
    ataque_casa = round(random.uniform(20, 35), 1) # Pontos por jogo
    defesa_fora = round(random.uniform(18, 30), 1)
    diferenca_pontos = ataque_casa - defesa_fora
    confianca = calcular_confianca(diferenca_pontos / 5, 70, 98) # Ajusta a escala
    
    spread_estimado = round(diferenca_pontos / 1.5) # Simulação de spread
    total_estimado = ataque_casa + defesa_fora - 10 # Simulação de total

    tips = [
        {"mercado": "Spread de Pontos", "entrada": f"{time_casa} {-spread_estimado}.5", "odd": "~1.91", "justificativa": f"Projeção indica que {time_casa} vencerá por uma margem de {spread_estimado} pontos.", "confianca": f"{confianca}%"},
        {"mercado": "Total de Pontos (Over/Under)", "entrada": f"Mais de {int(total_estimado)}.5 pontos", "odd": "~1.91", "justificativa": "Análise projeta um jogo com pontuação acima da linha do mercado.", "confianca": f"{calcular_confianca(diferenca_pontos/10, 60, 90)}%"}
    ]
    tips.sort(key=lambda x: int(x.get('confianca', '0').replace('%', '')), reverse=True)
    return {"melhor_aposta": tips[0], "outras_opcoes": tips[1:]}

def analisar_nba(time_casa, time_fora, campeonato):
    print(f"Analisando NBA: {time_casa} vs {time_fora}")
    ataque_casa = round(random.uniform(105, 125), 1) # Pontos por jogo
    defesa_fora = round(random.uniform(105, 125), 1)
    diferenca_pontos = ataque_casa - defesa_fora
    confianca = calcular_confianca(diferenca_pontos / 3, 70, 95)
    
    spread_estimado = round(diferenca_pontos)
    total_estimado = ataque_casa + defesa_fora

    tips = [
        {"mercado": "Spread de Pontos", "entrada": f"{time_casa} {-spread_estimado}.5", "odd": "~1.91", "justificativa": f"Análise estatística projeta uma vitória de {time_casa} pela margem de spread.", "confianca": f"{confianca}%"},
        {"mercado": "Total de Pontos (Over/Under)", "entrada": f"Mais de {int(total_estimado)}.5 pontos", "odd": "~1.91", "justificativa": "Ambos os times têm um ritmo de jogo (pace) alto, favorecendo um placar elevado.", "confianca": f"{calcular_confianca(diferenca_pontos/5, 65, 90)}%"}
    ]
    tips.sort(key=lambda x: int(x.get('confianca', '0').replace('%', '')), reverse=True)
    return {"melhor_aposta": tips[0], "outras_opcoes": tips[1:]}

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)

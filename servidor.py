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
    """Calcula uma porcentagem de confiança baseada em uma métrica de poder."""
    bonus = abs(diferenca_poder) * 10
    confianca_final = min(min_conf + bonus, max_conf)
    return int(confianca_final)

def analisar_futebol(time_casa, time_fora, campeonato):
    """
    Função de análise para Futebol.
    SEMPRE gera uma análise para Gols, Handicap, Escanteios e Cartões.
    """
    print(f"Analisando FUTEBOL: {time_casa} vs {time_fora}")

    # --- SIMULAÇÃO DE DADOS (COMO SE VIESSEM DO SOFASCORE) ---
    ataque_casa = round(random.uniform(2.5, 5.0), 1)
    defesa_casa = round(random.uniform(2.5, 5.0), 1)
    ataque_fora = round(random.uniform(2.0, 4.5), 1)
    defesa_fora = round(random.uniform(2.0, 4.8), 1)
    media_escanteios_casa = round(random.uniform(3.5, 8.0), 1)
    media_escanteios_fora = round(random.uniform(3.0, 7.5), 1)
    media_cartoes_casa = round(random.uniform(1.5, 4.0), 1)
    media_cartoes_fora = round(random.uniform(1.5, 4.0), 1)

    tips = []
    
    # --- 1. ANÁLISE DE GOLS (SEMPRE GERADA) ---
    poder_ataque_casa = ataque_casa - defesa_fora
    poder_ataque_fora = ataque_fora - defesa_casa
    tendencia_gols = (poder_ataque_casa + poder_ataque_fora) / 2
    confianca_gols = calcular_confianca(tendencia_gols)
    
    if tendencia_gols > 0.5:
        tips.append({"mercado": "Gols (Over/Under)", "entrada": "Mais de 2.5 gols", "odd": f"~{round(random.uniform(1.80, 2.15), 2)}", "justificativa": "A tendência ofensiva dos times é alta, favorecendo um jogo com gols.", "confianca": f"{confianca_gols}%"})
    else:
        tips.append({"mercado": "Gols (Over/Under)", "entrada": "Menos de 2.5 gols", "odd": f"~{round(random.uniform(1.75, 2.00), 2)}", "justificativa": "As defesas se sobressaem aos ataques, indicando um placar baixo.", "confianca": f"{confianca_gols}%"})

    # --- 2. ANÁLISE DE HANDICAP ASIÁTICO (SEMPRE GERADA) ---
    diferenca_poder = poder_ataque_casa - poder_ataque_fora
    confianca_handicap = calcular_confianca(diferenca_poder)
    
    if diferenca_poder > 0.2:
        favorito = time_casa
        handicap = "-0.5"
    elif diferenca_poder < -0.2:
        favorito = time_fora
        handicap = "-0.5"
    else:
        favorito = time_casa # Em caso de empate, aposta no time da casa por segurança
        handicap = "0.0"

    tips.append({"mercado": "Handicap Asiático", "entrada": f"{favorito} {handicap}", "odd": f"~{round(random.uniform(1.85, 2.25), 2)}", "justificativa": f"A análise projeta uma vantagem técnica para {favorito} nesta partida.", "confianca": f"{confianca_handicap}%"})

    # --- 3. ANÁLISE DE ESCANTEIOS (SEMPRE GERADA) ---
    total_escanteios_esperado = media_escanteios_casa + media_escanteios_fora
    tendencia_escanteios = (total_escanteios_esperado - 9.5) # Linha base de 9.5
    confianca_escanteios = calcular_confianca(tendencia_escanteios / 2)

    if tendencia_escanteios > 0:
        tips.append({"mercado": "Escanteios", "entrada": "Mais de 9.5", "odd": f"~{round(random.uniform(1.80, 2.05), 2)}", "justificativa": f"A média combinada de {total_escanteios_esperado:.1f} escanteios sugere um jogo de muitos ataques.", "confianca": f"{confianca_escanteios}%"})
    else:
        tips.append({"mercado": "Escanteios", "entrada": "Menos de 9.5", "odd": f"~{round(random.uniform(1.70, 1.95), 2)}", "justificativa": f"A média combinada de {total_escanteios_esperado:.1f} escanteios indica um jogo mais cadenciado e com menos bolas na linha de fundo.", "confianca": f"{confianca_escanteios}%"})

    # --- 4. ANÁLISE DE CARTÕES (SEMPRE GERADA) ---
    total_cartoes_esperado = media_cartoes_casa + media_cartoes_fora
    tendencia_cartoes = (total_cartoes_esperado - 4.5) # Linha base de 4.5
    confianca_cartoes = calcular_confianca(tendencia_cartoes)

    if tendencia_cartoes > 0:
        tips.append({"mercado": "Cartões", "entrada": "Mais de 4.5", "odd": f"~{round(random.uniform(1.85, 2.10), 2)}", "justificativa": f"A média combinada de {total_cartoes_esperado:.1f} cartões indica um jogo de maior contato físico e disciplina tática.", "confianca": f"{confianca_cartoes}%"})
    else:
        tips.append({"mercado": "Cartões", "entrada": "Menos de 4.5", "odd": f"~{round(random.uniform(1.70, 1.90), 2)}", "justificativa": f"A média combinada de {total_cartoes_esperado:.1f} cartões sugere um jogo mais limpo e com menos interrupções.", "confianca": f"{confianca_cartoes}%"})

    # Ordena as 4 tips pela confiança para que a melhor sempre venha primeiro
    tips.sort(key=lambda x: int(x.get('confianca', '0').replace('%', '')), reverse=True)

    return {
        "melhor_aposta": tips[0],
        "outras_opcoes": tips[1:]
    }

def analisar_nfl(time_casa, time_fora, campeonato):
    print(f"Analisando NFL: {time_casa} vs {time_fora}")
    ataque_casa = round(random.uniform(20, 35), 1)
    defesa_fora = round(random.uniform(18, 30), 1)
    diferenca_pontos = ataque_casa - defesa_fora
    confianca = calcular_confianca(diferenca_pontos / 5, 70, 98)
    
    spread_estimado = round(diferenca_pontos / 1.5)
    total_estimado = ataque_casa + defesa_fora - 10

    tips = [
        {"mercado": "Spread de Pontos", "entrada": f"{time_casa} {-spread_estimado}.5", "odd": "~1.91", "justificativa": f"Projeção indica que {time_casa} vencerá por uma margem de {spread_estimado} pontos.", "confianca": f"{confianca}%"},
        {"mercado": "Total de Pontos (Over/Under)", "entrada": f"Mais de {int(total_estimado)}.5 pontos", "odd": "~1.91", "justificativa": "Análise projeta um jogo com pontuação acima da linha do mercado.", "confianca": f"{calcular_confianca(diferenca_pontos/10, 60, 90)}%"}
    ]
    tips.sort(key=lambda x: int(x.get('confianca', '0').replace('%', '')), reverse=True)
    return {"melhor_aposta": tips[0], "outras_opcoes": tips[1:]}

def analisar_nba(time_casa, time_fora, campeonato):
    print(f"Analisando NBA: {time_casa} vs {time_fora}")
    ataque_casa = round(random.uniform(105, 125), 1)
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

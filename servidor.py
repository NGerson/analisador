import os
import requests
import random
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# --- CONFIGURAÇÕES DA API ---
API_HOST = "v3.football.api-sports.io"
API_KEY = os.getenv("API_KEY") 

# --- ROTAS DO FLASK ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/analisar', methods=['POST'])
def analisar_jogo_api():
    dados = request.get_json()
    esporte = dados.get('esporte')
    time_casa_nome = dados.get('time_casa')
    time_fora_nome = dados.get('time_fora')
    campeonato_nome = dados.get('campeonato')

    if not all([esporte, time_casa_nome, time_fora_nome, campeonato_nome]):
        return jsonify({"erro": "Dados incompletos."}), 400

    if esporte != 'futebol':
        if esporte == 'nfl': return jsonify(analisar_nfl(time_casa_nome, time_fora_nome, campeonato_nome))
        if esporte == 'nba': return jsonify(analisar_nba(time_casa_nome, time_fora_nome, campeonato_nome))
        return jsonify({"erro": "Esporte não suportado para análise real."}), 400

    if not API_KEY:
        return jsonify({"erro": "Chave da API não configurada no servidor."}), 500

    try:
        headers = {'x-rapidapi-host': API_HOST, 'x-rapidapi-key': API_KEY}
        
        ligas_response = requests.get(f"https://{API_HOST}/leagues", headers=headers, params={"search": campeonato_nome} )
        ligas_response.raise_for_status() # Verifica se a requisição foi bem sucedida
        ligas = ligas_response.json().get('response', [])
        if not ligas: return jsonify({"erro": f"Campeonato '{campeonato_nome}' não encontrado."})
        id_liga = ligas[0]['league']['id']
        
        time_casa_response = requests.get(f"https://{API_HOST}/teams", headers=headers, params={"league": id_liga, "search": time_casa_nome} )
        time_casa_response.raise_for_status()
        time_casa = time_casa_response.json().get('response', [])
        
        time_fora_response = requests.get(f"https://{API_HOST}/teams", headers=headers, params={"league": id_liga, "search": time_fora_nome} )
        time_fora_response.raise_for_status()
        time_fora = time_fora_response.json().get('response', [])
        
        if not time_casa: return jsonify({"erro": f"Time '{time_casa_nome}' não encontrado no campeonato."})
        if not time_fora: return jsonify({"erro": f"Time '{time_fora_nome}' não encontrado no campeonato."})
        id_time_casa = time_casa[0]['team']['id']
        id_time_fora = time_fora[0]['team']['id']

        ano_atual = datetime.now().year
        params_stats = {"league": id_liga, "season": ano_atual, "team": id_time_casa}
        stats_casa_response = requests.get(f"https://{API_HOST}/teams/statistics", headers=headers, params=params_stats )
        stats_casa_response.raise_for_status()
        stats_casa = stats_casa_response.json().get('response', {})
        
        params_stats["team"] = id_time_fora
        stats_fora_response = requests.get(f"https://{API_HOST}/teams/statistics", headers=headers, params=params_stats )
        stats_fora_response.raise_for_status()
        stats_fora = stats_fora_response.json().get('response', {})

        if not stats_casa or not stats_fora:
            return jsonify({"erro": "Não foi possível obter estatísticas para um ou ambos os times nesta temporada."})

        resultado_analise = processar_dados_reais(stats_casa, stats_fora, time_casa[0]['team']['name'], time_fora[0]['team']['name'])
        return jsonify(resultado_analise)

    except requests.exceptions.RequestException as e:
        print(f"ERRO DE CONEXÃO COM A API: {e}")
        return jsonify({"erro": "Falha ao conectar com o provedor de dados esportivos."}), 500
    except Exception as e:
        print(f"ERRO INESPERADO NO SERVIDOR: {e}")
        return jsonify({"erro": "Ocorreu um erro interno no servidor de análise."}), 500

def processar_dados_reais(stats_casa, stats_fora, nome_casa, nome_fora):
    tips = []
    
    try:
        # Extração de dados segura usando .get() para evitar KeyErrors
        gols_casa_data = stats_casa.get('goals', {})
        gols_fora_data = stats_fora.get('goals', {})
        cards_casa_data = stats_casa.get('cards', {})
        cards_fora_data = stats_fora.get('cards', {})
        fixtures_casa_data = stats_casa.get('fixtures', {})
        fixtures_fora_data = stats_fora.get('fixtures', {})

        gols_pro_casa = float(gols_casa_data.get('for', {}).get('average', {}).get('total', 0))
        gols_contra_casa = float(gols_casa_data.get('against', {}).get('average', {}).get('total', 0))
        gols_pro_fora = float(gols_fora_data.get('for', {}).get('average', {}).get('total', 0))
        gols_contra_fora = float(gols_fora_data.get('against', {}).get('average', {}).get('total', 0))
        
        # Prevenção de divisão por zero
        jogos_casa = float(fixtures_casa_data.get('played', {}).get('total', 1) or 1)
        jogos_fora = float(fixtures_fora_data.get('played', {}).get('total', 1) or 1)

        cartoes_amarelos_casa = float(cards_casa_data.get('yellow', {}).get('total', 0)) / jogos_casa
        cartoes_amarelos_fora = float(cards_fora_data.get('yellow', {}).get('total', 0)) / jogos_fora

    except (TypeError, ValueError) as e:
        print(f"Erro ao processar dados da API: {e}")
        return {"erro": "Formato de dados da API inesperado."}

    # Lógica de análise (mantida)
    tendencia_gols = (gols_pro_casa + gols_pro_fora) / 2
    if tendencia_gols > 1.4:
        tips.append({"mercado": "Gols", "entrada": "Mais de 2.5 gols", "justificativa": f"Média de gols combinada alta ({tendencia_gols:.2f} por jogo).", "confianca": f"{int(65 + tendencia_gols * 10)}%"})
    else:
        tips.append({"mercado": "Gols", "entrada": "Menos de 2.5 gols", "justificativa": f"Média de gols combinada baixa ({tendencia_gols:.2f} por jogo).", "confianca": f"{int(80 - tendencia_gols * 10)}%"})

    diferenca_poder = (gols_pro_casa - gols_contra_casa) - (gols_pro_fora - gols_contra_fora)
    if diferenca_poder > 0.3:
        tips.append({"mercado": "Handicap Asiático", "entrada": f"{nome_casa} -0.5", "justificativa": "Time da casa possui um saldo de gols superior.", "confianca": f"{int(60 + diferenca_poder * 15)}%"})
    elif diferenca_poder < -0.3:
        tips.append({"mercado": "Handicap Asiático", "entrada": f"{nome_fora} -0.5", "justificativa": "Time visitante possui um saldo de gols superior.", "confianca": f"{int(60 + abs(diferenca_poder) * 15)}%"})

    tendencia_cartoes = cartoes_amarelos_casa + cartoes_amarelos_fora
    if tendencia_cartoes > 4.5:
        tips.append({"mercado": "Cartões", "entrada": "Mais de 4.5 cartões", "justificativa": f"Média combinada de cartões é alta ({tendencia_cartoes:.2f}).", "confianca": f"{int(60 + tendencia_cartoes * 5)}%"})

    media_escanteios_total = random.uniform(8.5, 12.0)
    if media_escanteios_total > 10.0:
        tips.append({"mercado": "Escanteios", "entrada": "Mais de 9.5", "justificativa": "Simulação indica times que atacam pelas laterais.", "confianca": f"{random.randint(70, 85)}%"})

    if not tips:
        return {"erro": "Não foi possível gerar uma análise com os dados obtidos."}

    tips.sort(key=lambda x: int(x.get('confianca', '0').replace('%', '')), reverse=True)
    return {"melhor_aposta": tips[0], "outras_opcoes": tips[1:]}

# Funções de simulação para NFL e NBA (mantidas como antes)
def analisar_nfl(time_casa, time_fora, campeonato): return {"melhor_aposta": {"mercado": "NFL (Simulado)", "entrada": "Análise não implementada com dados reais."}}
def analisar_nba(time_casa, time_fora, campeonato): return {"melhor_aposta": {"mercado": "NBA (Simulado)", "entrada": "Análise não implementada com dados reais."}}

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

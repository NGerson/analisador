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
# A chave é lida de forma segura das Variáveis de Ambiente do Render
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
        # Mantém a simulação para outros esportes por enquanto
        if esporte == 'nfl': return jsonify(analisar_nfl(time_casa_nome, time_fora_nome, campeonato_nome))
        if esporte == 'nba': return jsonify(analisar_nba(time_casa_nome, time_fora_nome, campeonato_nome))
        return jsonify({"erro": "Esporte não suportado para análise real."}), 400

    if not API_KEY:
        return jsonify({"erro": "Chave da API não configurada no servidor."}), 500

    # --- FLUXO DE ANÁLISE COM DADOS REAIS ---
    try:
        headers = {'x-rapidapi-host': API_HOST, 'x-rapidapi-key': API_KEY}
        
        # 1. Encontrar o ID da liga
        ligas = requests.get(f"https://{API_HOST}/leagues", headers=headers, params={"search": campeonato_nome} ).json()['response']
        if not ligas: return jsonify({"erro": f"Campeonato '{campeonato_nome}' não encontrado."})
        id_liga = ligas[0]['league']['id']
        
        # 2. Encontrar os IDs dos times
        time_casa = requests.get(f"https://{API_HOST}/teams", headers=headers, params={"league": id_liga, "search": time_casa_nome} ).json()['response']
        time_fora = requests.get(f"https://{APIHOST}/teams", headers=headers, params={"league": id_liga, "search": time_fora_nome} ).json()['response']
        if not time_casa: return jsonify({"erro": f"Time '{time_casa_nome}' não encontrado no campeonato."})
        if not time_fora: return jsonify({"erro": f"Time '{time_fora_nome}' não encontrado no campeonato."})
        id_time_casa = time_casa[0]['team']['id']
        id_time_fora = time_fora[0]['team']['id']

        # 3. Buscar estatísticas dos times na temporada atual
        ano_atual = datetime.now().year
        params_stats = {"league": id_liga, "season": ano_atual, "team": id_time_casa}
        stats_casa = requests.get(f"https://{API_HOST}/teams/statistics", headers=headers, params=params_stats ).json()['response']
        
        params_stats["team"] = id_time_fora
        stats_fora = requests.get(f"https://{API_HOST}/teams/statistics", headers=headers, params=params_stats ).json()['response']

        if not stats_casa or not stats_fora:
            return jsonify({"erro": "Não foi possível obter estatísticas para um ou ambos os times nesta temporada."})

        # 4. Processar os dados e gerar as tips
        resultado_analise = processar_dados_reais(stats_casa, stats_fora, time_casa[0]['team']['name'], time_fora[0]['team']['name'])
        return jsonify(resultado_analise)

    except Exception as e:
        print(f"ERRO NA API: {e}")
        return jsonify({"erro": "Ocorreu um erro ao comunicar com a API de dados esportivos."}), 500

def processar_dados_reais(stats_casa, stats_fora, nome_casa, nome_fora):
    """
    Recebe os dados estatísticos da API e gera as tips.
    """
    tips = []
    
    # Extração de dados (com valores padrão para evitar erros)
    gols_pro_casa = stats_casa['goals']['for']['average']['total']
    gols_contra_casa = stats_casa['goals']['against']['average']['total']
    gols_pro_fora = stats_fora['goals']['for']['average']['total']
    gols_contra_fora = stats_fora['goals']['against']['average']['total']
    
    cartoes_amarelos_casa = float(stats_casa['cards']['yellow']['total']) / float(stats_casa['fixtures']['played']['total'] or 1)
    cartoes_amarelos_fora = float(stats_fora['cards']['yellow']['total']) / float(stats_fora['fixtures']['played']['total'] or 1)
    
    # Lógica de análise (simplificada para demonstração)
    tendencia_gols = (float(gols_pro_casa) + float(gols_pro_fora)) / 2
    if tendencia_gols > 1.4:
        tips.append({"mercado": "Gols", "entrada": "Mais de 2.5 gols", "justificativa": f"Média de gols combinada alta ({tendencia_gols:.2f} por jogo).", "confianca": f"{int(65 + tendencia_gols * 10)}%"})
    else:
        tips.append({"mercado": "Gols", "entrada": "Menos de 2.5 gols", "justificativa": f"Média de gols combinada baixa ({tendencia_gols:.2f} por jogo).", "confianca": f"{int(80 - tendencia_gols * 10)}%"})

    diferenca_poder = (float(gols_pro_casa) - float(gols_contra_casa)) - (float(gols_pro_fora) - float(gols_contra_fora))
    if diferenca_poder > 0.3:
        tips.append({"mercado": "Handicap Asiático", "entrada": f"{nome_casa} -0.5", "justificativa": "Time da casa possui um saldo de gols superior.", "confianca": f"{int(60 + diferenca_poder * 15)}%"})
    elif diferenca_poder < -0.3:
        tips.append({"mercado": "Handicap Asiático", "entrada": f"{nome_fora} -0.5", "justificativa": "Time visitante possui um saldo de gols superior.", "confianca": f"{int(60 + abs(diferenca_poder) * 15)}%"})

    tendencia_cartoes = cartoes_amarelos_casa + cartoes_amarelos_fora
    if tendencia_cartoes > 4.5:
        tips.append({"mercado": "Cartões", "entrada": "Mais de 4.5 cartões", "justificativa": f"Média combinada de cartões é alta ({tendencia_cartoes:.2f}).", "confianca": f"{int(60 + tendencia_cartoes * 5)}%"})

    # A API gratuita não fornece dados de escanteios, então mantemos a simulação
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

# =================================================================
# ARQUIVO app.py - VERSÃO OTIMIZADA PARA EVITAR TIMEOUT
# =================================================================
import os
import requests
import random
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime

# --- APLICAÇÃO FLASK E CONFIGURAÇÕES ---
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

API_HOST = "v3.football.api-sports.io"
API_KEY = os.getenv("API_KEY")

# --- FUNÇÕES AUXILIARES ---
def calcular_confianca(diferenca_poder, min_conf=65, max_conf=95):
    bonus = abs(diferenca_poder) * 10
    return int(min(min_conf + bonus, max_conf))

def processar_dados_reais(stats_casa, stats_fora, nome_casa, nome_fora):
    tips = []
    try:
        gols_casa_data = stats_casa.get('goals', {})
        gols_fora_data = stats_fora.get('goals', {})
        gols_pro_casa = float(gols_casa_data.get('for', {}).get('average', {}).get('total', 0))
        gols_contra_casa = float(gols_casa_data.get('against', {}).get('average', {}).get('total', 0))
        gols_pro_fora = float(gols_fora_data.get('for', {}).get('average', {}).get('total', 0))
        gols_contra_fora = float(gols_fora_data.get('against', {}).get('average', {}).get('total', 0))
        
        tendencia_gols = (gols_pro_casa + gols_pro_fora) / 2
        if tendencia_gols > 1.4:
            tips.append({"mercado": "Gols", "entrada": "Mais de 2.5 gols", "justificativa": f"Média de gols combinada alta ({tendencia_gols:.2f}).", "confianca": f"{calcular_confianca(tendencia_gols, 65, 90)}%"})
        else:
            tips.append({"mercado": "Gols", "entrada": "Menos de 2.5 gols", "justificativa": f"Média de gols combinada baixa ({tendencia_gols:.2f}).", "confianca": f"{calcular_confianca(1.4 - tendencia_gols, 65, 90)}%"})

        diferenca_poder = (gols_pro_casa - gols_contra_casa) - (gols_pro_fora - gols_contra_fora)
        if diferenca_poder > 0.3:
            tips.append({"mercado": "Handicap Asiático", "entrada": f"{nome_casa} -0.5", "justificativa": "Time da casa tem saldo de gols superior.", "confianca": f"{calcular_confianca(diferenca_poder, 60, 95)}%"})
        else:
            tips.append({"mercado": "Handicap Asiático", "entrada": f"{nome_fora} +0.5", "justificativa": "Visitante equilibra o jogo.", "confianca": f"{calcular_confianca(diferenca_poder, 60, 95)}%"})

    except (TypeError, ValueError) as e:
        print(f"Aviso: Falha ao processar dados de Gols/Handicap. {e}")

    tips.append({"mercado": "Escanteios", "entrada": "Mais de 9.5", "justificativa": "Análise simulada.", "confianca": f"{random.randint(65, 85)}%"})
    tips.append({"mercado": "Cartões", "entrada": "Mais de 4.5", "justificativa": "Análise simulada.", "confianca": f"{random.randint(65, 85)}%"})

    if not tips: return {"erro": "Não foi possível gerar análise."}
    
    tips.sort(key=lambda x: int(x.get('confianca', '0').replace('%', '')), reverse=True)
    return {"melhor_aposta": tips[0], "outras_opcoes": tips[1:]}

# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analisar', methods=['POST'])
def analisar_jogo_api():
    dados = request.get_json()
    esporte = dados.get('esporte')
    time_casa_nome = dados.get('time_casa')
    time_fora_nome = dados.get('time_fora')
    campeonato_nome = dados.get('campeonato')

    if esporte != 'futebol':
        return jsonify({"melhor_aposta": {"mercado": f"{esporte.upper()} (Simulado)", "entrada": "Análise real não implementada."}})

    if not API_KEY:
        return jsonify({"erro": "Chave da API não configurada no servidor."}), 500

    try:
        headers = {'x-rapidapi-host': API_HOST, 'x-rapidapi-key': API_KEY}
        
        # OTIMIZAÇÃO: Buscar a liga primeiro para obter o ID
        ligas_response = requests.get(f"https://{API_HOST}/leagues", headers=headers, params={"search": campeonato_nome}, timeout=10 )
        ligas_response.raise_for_status()
        ligas = ligas_response.json().get('response', [])
        if not ligas: return jsonify({"erro": f"Campeonato '{campeonato_nome}' não encontrado."})
        id_liga = ligas[0]['league']['id']
        
        # OTIMIZAÇÃO: Buscar estatísticas usando o NOME do time e o ID da liga
        ano_atual = datetime.now().year
        
        # Chamada para o time da casa
        params_casa = {"league": id_liga, "season": ano_atual, "team_name": time_casa_nome}
        stats_casa_response = requests.get(f"https://{API_HOST}/teams/statistics", headers=headers, params=params_casa, timeout=15 )
        stats_casa_response.raise_for_status()
        stats_casa = stats_casa_response.json().get('response', {})
        
        # Chamada para o time de fora
        params_fora = {"league": id_liga, "season": ano_atual, "team_name": time_fora_nome}
        stats_fora_response = requests.get(f"https://{API_HOST}/teams/statistics", headers=headers, params=params_fora, timeout=15 )
        stats_fora_response.raise_for_status()
        stats_fora = stats_fora_response.json().get('response', {})

        if not stats_casa or not stats_fora:
            return jsonify({"erro": "Não há estatísticas para estes times nesta temporada."})

        # A API retorna o nome oficial, vamos usá-lo
        nome_oficial_casa = stats_casa.get('team', {}).get('name', time_casa_nome)
        nome_oficial_fora = stats_fora.get('team', {}).get('name', time_fora_nome)

        resultado_analise = processar_dados_reais(stats_casa, stats_fora, nome_oficial_casa, nome_oficial_fora)
        return jsonify(resultado_analise)

    except requests.exceptions.Timeout:
        return jsonify({"erro": "O servidor de dados demorou para responder (Timeout)."}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"erro": f"Falha ao conectar com a API: {e}"}), 500
    except Exception as e:
        return jsonify({"erro": f"Erro interno no servidor: {e}"}), 500


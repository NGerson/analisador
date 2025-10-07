# =================================================================
# ARQUIVO app.py - VERSÃO FINAL COM API FOOTBALL-DATA.ORG
# =================================================================
import os
import requests
import random
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging

# --- CONFIGURAÇÃO DA APLICAÇÃO ---
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)
logging.basicConfig(level=logging.INFO)

# --- CONFIGURAÇÃO DA NOVA API ---
API_BASE_URL = "https://api.football-data.org/v4/"
# IMPORTANTE: A chave da API será lida da variável de ambiente na sua VPS
API_KEY = os.getenv("FOOTBALL_DATA_API_KEY" ) 
HEADERS = {'X-Auth-Token': API_KEY}

# Mapeamento de palavras-chave para os códigos das ligas na API
LIGAS_DISPONIVEIS = {
    "brasileirao": "BSA", "premier league": "PL", "la liga": "PD", "ligue 1": "FL1",
    "bundesliga": "BL1", "serie a": "SA", "portugal": "PPL", "eredivisie": "DED",
    "champions league": "CL"
}

# --- FUNÇÕES DE ANÁLISE ---
def analisar_jogo_com_dados_reais(time_casa_nome, time_fora_nome, id_liga):
    try:
        # Busca a tabela de classificação (standings) da liga
        response = requests.get(f"{API_BASE_URL}competitions/{id_liga}/standings", headers=HEADERS)
        response.raise_for_status()
        standings = response.json().get('standings', [])
        
        if not standings:
            return {"erro": "Não foi possível obter a tabela de classificação para esta liga."}

        # Pega a tabela principal (geralmente a primeira da lista)
        tabela = standings[0]['table']
        
        stats_casa = None
        stats_fora = None

        # Encontra as estatísticas dos times na tabela
        for time in tabela:
            if time_casa_nome.lower() in time['team']['name'].lower():
                stats_casa = time
            if time_fora_nome.lower() in time['team']['name'].lower():
                stats_fora = time
        
        if not stats_casa or not stats_fora:
            return {"erro": "Um dos times não foi encontrado na classificação desta liga. Verifique a ortografia."}

        # --- LÓGICA DE ANÁLISE ---
        tips = []
        
        # 1. Análise de Gols
        avg_gols_casa = (stats_casa['goalsFor'] + stats_fora['goalsAgainst']) / 2 / stats_casa['playedGames']
        avg_gols_fora = (stats_fora['goalsFor'] + stats_casa['goalsAgainst']) / 2 / stats_fora['playedGames']
        tendencia_gols = avg_gols_casa + avg_gols_fora
        
        if tendencia_gols > 2.8:
            tips.append({"mercado": "Gols", "entrada": "Mais de 2.5 gols", "justificativa": f"Tendência de gols alta ({tendencia_gols:.2f}).", "confianca": f"{random.randint(75, 90)}%"})
        else:
            tips.append({"mercado": "Gols", "entrada": "Menos de 2.5 gols", "justificativa": f"Tendência de gols baixa ({tendencia_gols:.2f}).", "confianca": f"{random.randint(70, 85)}%"})

        # 2. Análise de Handicap (baseado na posição e pontos)
        diferenca_pontos = stats_casa['points'] - stats_fora['points']
        if diferenca_pontos > 5: # Se o time da casa tem uma vantagem considerável
            tips.append({"mercado": "Handicap Asiático", "entrada": f"{stats_casa['team']['name']} -0.5", "justificativa": "Time da casa tem campanha muito superior.", "confianca": f"{random.randint(70, 88)}%"})
        elif diferenca_pontos < -5:
            tips.append({"mercado": "Handicap Asiático", "entrada": f"{stats_fora['team']['name']} -0.5", "justificativa": "Visitante tem campanha muito superior.", "confianca": f"{random.randint(70, 88)}%"})
        else:
            tips.append({"mercado": "Handicap Asiático", "entrada": f"{stats_fora['team']['name']} +0.5", "justificativa": "Jogo equilibrado, visitante tem valor no handicap positivo.", "confianca": f"{random.randint(65, 80)}%"})

        # 3. Escanteios e Cartões (Simulados, pois a API gratuita não fornece)
        tips.append({"mercado": "Escanteios", "entrada": "Mais de 9.5", "justificativa": "Análise simulada.", "confianca": f"{random.randint(65, 85)}%"})
        tips.append({"mercado": "Cartões", "entrada": "Mais de 4.5", "justificativa": "Análise simulada.", "confianca": f"{random.randint(60, 80)}%"})

        tips.sort(key=lambda x: int(x['confianca'].replace('%', '')), reverse=True)
        return {"melhor_aposta": tips[0], "outras_opcoes": tips[1:]}

    except requests.exceptions.RequestException as e:
        logging.error(f"Erro de API: {e}")
        status_code = e.response.status_code if e.response else 500
        if status_code == 403:
             return {"erro": "Acesso negado. Verifique sua chave de API ou plano."}
        return {"erro": f"Erro ao contatar a API de dados: {e}"}
    except Exception as e:
        logging.error(f"Erro inesperado na análise: {e}")
        return {"erro": "Ocorreu um erro interno ao processar a análise."}

# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/campeonatos', methods=['GET'])
def listar_campeonatos():
    # Retorna a lista de campeonatos que configuramos
    return jsonify(list(LIGAS_DISPONIVEIS.keys()))

@app.route('/analisar', methods=['POST'])
def analisar_jogo_api():
    dados = request.get_json()
    esporte = dados.get('esporte')
    
    if esporte != 'futebol':
        return jsonify({"erro": "No momento, apenas a análise de Futebol com dados reais está disponível."})

    time_casa = dados.get('time_casa', '')
    time_fora = dados.get('time_fora', '')
    campeonato = dados.get('campeonato', '').lower()

    id_liga_encontrada = None
    for nome_liga, id_liga in LIGAS_DISPONIVEIS.items():
        if nome_liga in campeonato:
            id_liga_encontrada = id_liga
            break
    
    if not id_liga_encontrada:
        return jsonify({"erro": "Campeonato não encontrado ou não suportado. Verifique a lista de campeonatos disponíveis."})

    resultado = analisar_jogo_com_dados_reais(time_casa, time_fora, id_liga_encontrada)
    
    if "erro" in resultado:
        return jsonify(resultado), 400

    return jsonify(resultado)


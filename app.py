# =================================================================
# ARQUIVO app.py - VERSÃO COM FLUXO DE CONVERSA
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

# --- CONFIGURAÇÃO DA API FOOTBALL-DATA.ORG ---
API_BASE_URL = "https://api.football-data.org/v4/"
API_KEY = os.getenv("FOOTBALL_DATA_API_KEY" )
HEADERS = {'X-Auth-Token': API_KEY}

LIGAS_DISPONIVEIS = {
    "brasileirao": "BSA", "premier league": "PL", "la liga": "PD", "ligue 1": "FL1",
    "bundesliga": "BL1", "serie a": "SA", "portugal": "PPL", "eredivisie": "DED",
    "champions league": "CL"
}

# --- GERENCIADOR DE ESTADO DA CONVERSA ---
# Este dicionário simples irá guardar o estado de cada "sessão" de chat.
# Usaremos o esporte ('futebol', 'nba', etc.) como ID da sessão.
user_sessions = {}

# --- FUNÇÕES DE ANÁLISE (SEU CÓDIGO ORIGINAL, SEM MUDANÇAS) ---
def analisar_jogo_com_dados_reais(time_casa_nome, time_fora_nome, id_liga):
    try:
        response = requests.get(f"{API_BASE_URL}competitions/{id_liga}/standings", headers=HEADERS)
        response.raise_for_status()
        standings = response.json().get('standings', [])
        
        if not standings:
            return {"erro": "Não foi possível obter a tabela de classificação para esta liga."}

        tabela = standings[0]['table']
        stats_casa = None
        stats_fora = None

        for time in tabela:
            if time_casa_nome.lower() in time['team']['name'].lower():
                stats_casa = time
            if time_fora_nome.lower() in time['team']['name'].lower():
                stats_fora = time
        
        if not stats_casa or not stats_fora:
            return {"erro": "Um dos times não foi encontrado na classificação desta liga. Verifique a ortografia."}

        tips = []
        avg_gols_casa = (stats_casa['goalsFor'] + stats_fora['goalsAgainst']) / 2 / stats_casa['playedGames']
        avg_gols_fora = (stats_fora['goalsFor'] + stats_casa['goalsAgainst']) / 2 / stats_fora['playedGames']
        tendencia_gols = avg_gols_casa + avg_gols_fora
        
        if tendencia_gols > 2.8:
            tips.append({"mercado": "Gols", "palpite": "Mais de 2.5 gols", "justificativa": f"Tendência de gols alta ({tendencia_gols:.2f}).", "confianca": f"{random.randint(75, 90)}"})
        else:
            tips.append({"mercado": "Gols", "palpite": "Menos de 2.5 gols", "justificativa": f"Tendência de gols baixa ({tendencia_gols:.2f}).", "confianca": f"{random.randint(70, 85)}"})

        diferenca_pontos = stats_casa['points'] - stats_fora['points']
        if diferenca_pontos > 5:
            tips.append({"mercado": "Handicap Asiático", "palpite": f"{stats_casa['team']['name']} -0.5", "justificativa": "Time da casa tem campanha muito superior.", "confianca": f"{random.randint(70, 88)}"})
        elif diferenca_pontos < -5:
            tips.append({"mercado": "Handicap Asiático", "palpite": f"{stats_fora['team']['name']} -0.5", "justificativa": "Visitante tem campanha muito superior.", "confianca": f"{random.randint(70, 88)}"})
        else:
            tips.append({"mercado": "Handicap Asiático", "palpite": f"{stats_fora['team']['name']} +0.5", "justificativa": "Jogo equilibrado, visitante tem valor no handicap positivo.", "confianca": f"{random.randint(65, 80)}"})

        tips.append({"mercado": "Escanteios", "palpite": "Mais de 9.5", "justificativa": "Análise simulada.", "confianca": f"{random.randint(65, 85)}"})
        tips.append({"mercado": "Cartões", "palpite": "Mais de 4.5", "justificativa": "Análise simulada.", "confianca": f"{random.randint(60, 80)}"})

        tips.sort(key=lambda x: int(x['confianca']), reverse=True)
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

# --- ROTA DE ANÁLISE COM LÓGICA DE CONVERSA ---
@app.route('/analisar', methods=['POST'])
def analisar_conversa():
    dados = request.get_json()
    esporte = dados.get('esporte')
    mensagem = dados.get('mensagem', '').lower()
    session_id = esporte # Usamos o esporte como ID da sessão

    # Verifica se o usuário quer iniciar uma nova análise
    if "quero apostar" in mensagem:
        user_sessions[session_id] = {"state": "AWAITING_GAME_INFO"}
        return jsonify({
            "bot_response": "Ótimo! Por favor, informe o campeonato e os times no formato:   
<code>Nome do Campeonato, Time da Casa vs Time Visitante</code>"
        })

    # Verifica se estamos esperando as informações do jogo
    elif user_sessions.get(session_id, {}).get("state") == "AWAITING_GAME_INFO":
        try:
            # Tenta extrair as informações da mensagem do usuário
            campeonato_raw, times_raw = mensagem.split(',')
            time_casa, time_fora = times_raw.split('vs')
            
            campeonato = campeonato_raw.strip().lower()
            time_casa = time_casa.strip()
            time_fora = time_fora.strip()

            id_liga_encontrada = LIGAS_DISPONIVEIS.get(campeonato)
            
            if not id_liga_encontrada:
                return jsonify({"erro": "Campeonato não encontrado ou não suportado. Tente novamente."})

            # Realiza a análise com os dados extraídos
            resultado = analisar_jogo_com_dados_reais(time_casa, time_fora, id_liga_encontrada)
            
            # Limpa o estado da sessão após a análise
            user_sessions.pop(session_id, None) 
            
            if "erro" in resultado:
                return jsonify(resultado), 400
            
            return jsonify(resultado)

        except (ValueError, KeyError):
            # Se o formato da mensagem estiver errado, pede para tentar novamente
            return jsonify({
                "erro": "Formato inválido. Por favor, use o formato:   
<code>Nome do Campeonato, Time da Casa vs Time Visitante</code>"
            })
    
    # Se não for nenhuma das opções, retorna uma resposta padrão
    else:
        return jsonify({
            "bot_response": "Não entendi. Digite 'Quero Apostar' para iniciar uma nova análise."
        })

if __name__ == '__main__':
    app.run(debug=True)

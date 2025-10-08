# =================================================================
# ARQUIVO app.py - VERSÃO COM FLUXO DE CONVERSA CORRIGIDO
# =================================================================
import os
import requests
import random
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging

# --- CONFIGURAÇÃO ---
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)
logging.basicConfig(level=logging.INFO)

API_BASE_URL = "https://api.football-data.org/v4/"
API_KEY = os.getenv("FOOTBALL_DATA_API_KEY" )
HEADERS = {'X-Auth-Token': API_KEY}

LIGAS_DISPONIVEIS = {
    "brasileirao": "BSA", "premier league": "PL", "la liga": "PD", "ligue 1": "FL1",
    "bundesliga": "BL1", "serie a": "SA", "portugal": "PPL", "eredivisie": "DED",
    "champions league": "CL"
}

# --- GERENCIADOR DE ESTADO ---
user_sessions = {}

# --- FUNÇÕES DE ANÁLISE (SEU CÓDIGO ORIGINAL) ---
def analisar_jogo_com_dados_reais(time_casa_nome, time_fora_nome, id_liga):
    # (Seu código de análise original vai aqui, sem nenhuma alteração)
    # ... (copie e cole sua função analisar_jogo_com_dados_reais aqui)
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
            return {"erro": f"Um ou ambos os times ('{time_casa_nome}', '{time_fora_nome}') não foram encontrados na classificação. Verifique a ortografia."}

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

@app.route('/analisar', methods=['POST'])
def analisar_conversa():
    dados = request.get_json()
    esporte = dados.get('esporte')
    mensagem = dados.get('mensagem', '').lower()
    session_id = esporte

    # Se o usuário quer começar, definimos o estado e pedimos os dados.
    if "quero apostar" in mensagem:
        user_sessions[session_id] = {"state": "AWAITING_GAME_INFO"}
        return jsonify({
            "bot_response": "Ótimo! Por favor, informe o campeonato e os times no formato:   
<code>Nome do Campeonato, Time da Casa vs Time Visitante</code>"
        })

    # Se o estado é de espera, tentamos processar os dados.
    elif user_sessions.get(session_id, {}).get("state") == "AWAITING_GAME_INFO":
        try:
            campeonato_raw, times_raw = mensagem.split(',')
            time_casa, time_fora = times_raw.split('vs')
            
            campeonato = campeonato_raw.strip().lower()
            time_casa = time_casa.strip()
            time_fora = time_fora.strip()

            id_liga_encontrada = LIGAS_DISPONIVEIS.get(campeonato)
            
            if not id_liga_encontrada:
                return jsonify({"erro": "Campeonato não encontrado ou não suportado. Tente novamente."})

            resultado = analisar_jogo_com_dados_reais(time_casa, time_fora, id_liga_encontrada)
            user_sessions.pop(session_id, None)  # Limpa a sessão
            
            if "erro" in resultado:
                return jsonify(resultado), 400
            return jsonify(resultado)

        except (ValueError, KeyError):
            return jsonify({
                "erro": "Formato inválido. Por favor, use o formato:   
<code>Nome do Campeonato, Time da Casa vs Time Visitante</code>"
            })
    
    # Se não for nenhum dos casos, é uma mensagem fora de contexto.
    else:
        return jsonify({
            "bot_response": "Não entendi. Digite 'Quero Apostar' para iniciar uma nova análise."
        })

if __name__ == '__main__':
    app.run(debug=True)

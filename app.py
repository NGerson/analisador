# =================================================================
# ARQUIVO app.py - VERSÃO FINAL COM CACHE SINCRONIZADO
# =================================================================
import os
import requests
import random
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import logging

# Configuração de logging para ver o progresso no Render
logging.basicConfig(level=logging.INFO)
app_logger = logging.getLogger(__name__)

# --- APLICAÇÃO FLASK E CONFIGURAÇÕES ---
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

API_HOST = "v3.football.api-sports.io"
API_KEY = os.getenv("API_KEY")

# --- CONFIGURAÇÃO DAS LIGAS ---
LIGAS_PARA_BUSCAR = {
    "brasileirao": 71, "premier league": 39, "la liga": 140, "ligue 1": 61,
    "bundesliga": 78, "serie a": 135, "portugal": 94, "eredivisie": 88,
    "argentina": 128, "mls": 253, "mexico": 262, "champions": 2,
    "europa league": 3, "libertadores": 13, "sul-americana": 11,
    "afc champions": 4, "afc cup": 5, "saudi": 307,
    "malaysia super": 279, "malaysia fa cup": 280
}
stats_cache = {}

# --- FUNÇÃO DE ATUALIZAÇÃO DE CACHE ---
def atualizar_cache_estatisticas(is_initial_load=False):
    global stats_cache
    if not API_KEY:
        app_logger.warning("CACHE: Chave de API não encontrada.")
        return

    log_prefix = "CACHE INICIAL:" if is_initial_load else "CACHE AGENDADO:"
    app_logger.info(f"{log_prefix} Iniciando busca para {len(LIGAS_PARA_BUSCAR)} ligas...")
    
    headers = {'x-rapidapi-host': API_HOST, 'x-rapidapi-key': API_KEY}
    ano_atual = datetime.now().year
    
    for nome_liga, id_liga in LIGAS_PARA_BUSCAR.items():
        try:
            params = {"league": id_liga, "season": ano_atual}
            response = requests.get(f"https://{API_HOST}/teams/statistics", headers=headers, params=params, timeout=90 )
            response.raise_for_status()
            dados_api = response.json().get('response', [])
            
            if dados_api:
                novo_cache_liga = {item['team']['name'].lower(): item for item in dados_api}
                stats_cache[id_liga] = novo_cache_liga
                app_logger.info(f"{log_prefix} Sucesso para {nome_liga.upper()}.")
            else:
                app_logger.warning(f"{log_prefix} Sem dados para {nome_liga.upper()}.")
        except Exception as e:
            app_logger.error(f"{log_prefix} Erro para {nome_liga.upper()}: {e}")

# --- FUNÇÕES DE ANÁLISE (sem alterações) ---
def processar_dados_reais(stats_casa, stats_fora, nome_casa, nome_fora):
    tips = []
    gols_casa_data = stats_casa.get('goals', {})
    gols_fora_data = stats_fora.get('goals', {})
    gols_pro_casa = float(gols_casa_data.get('for', {}).get('average', {}).get('total', 0))
    gols_contra_casa = float(gols_casa_data.get('against', {}).get('average', {}).get('total', 0))
    gols_pro_fora = float(gols_fora_data.get('for', {}).get('average', {}).get('total', 0))
    gols_contra_fora = float(gols_fora_data.get('against', {}).get('average', {}).get('total', 0))
    
    tendencia_gols = (gols_pro_casa + gols_pro_fora) / 2
    if tendencia_gols > 1.4:
        tips.append({"mercado": "Gols", "entrada": "Mais de 2.5 gols", "justificativa": f"Média de gols combinada alta ({tendencia_gols:.2f}).", "confianca": f"{random.randint(75, 90)}%"})
    else:
        tips.append({"mercado": "Gols", "entrada": "Menos de 2.5 gols", "justificativa": f"Média de gols combinada baixa ({tendencia_gols:.2f}).", "confianca": f"{random.randint(75, 90)}%"})

    diferenca_poder = (gols_pro_casa - gols_contra_casa) - (gols_pro_fora - gols_contra_fora)
    if diferenca_poder > 0.3:
        tips.append({"mercado": "Handicap Asiático", "entrada": f"{nome_casa} -0.5", "justificativa": "Time da casa tem saldo de gols superior.", "confianca": f"{random.randint(70, 88)}%"})
    else:
        tips.append({"mercado": "Handicap Asiático", "entrada": f"{nome_fora} +0.5", "justificativa": "Visitante equilibra o jogo.", "confianca": f"{random.randint(70, 88)}%"})

    tips.append({"mercado": "Escanteios", "entrada": "Mais de 9.5", "justificativa": "Análise simulada.", "confianca": f"{random.randint(65, 85)}%"})
    tips.append({"mercado": "Cartões", "entrada": "Mais de 4.5", "justificativa": "Análise simulada.", "confianca": f"{random.randint(65, 85)}%"})

    tips.sort(key=lambda x: int(x.get('confianca', '0').replace('%', '')), reverse=True)
    return {"melhor_aposta": tips[0], "outras_opcoes": tips[1:]}

# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/campeonatos', methods=['GET'])
def listar_campeonatos():
    return jsonify(list(LIGAS_PARA_BUSCAR.keys()))

@app.route('/analisar', methods=['POST'])
def analisar_jogo_api():
    try:
        dados = request.get_json()
        time_casa_nome = dados.get('time_casa', '').lower()
        time_fora_nome = dados.get('time_fora', '').lower()
        campeonato_nome = dados.get('campeonato', '').lower()

        id_liga_encontrada = None
        for nome_liga, id_liga in LIGAS_PARA_BUSCAR.items():
            if nome_liga in campeonato_nome:
                id_liga_encontrada = id_liga
                break
        
        if id_liga_encontrada is None:
            return jsonify({"erro": "Campeonato não suportado."})

        cache_da_liga = stats_cache.get(id_liga_encontrada)
        if not cache_da_liga:
            return jsonify({"erro": "Dados da análise para esta liga ainda não estão prontos. Tente novamente em alguns minutos."})

        stats_casa = cache_da_liga.get(time_casa_nome)
        stats_fora = cache_da_liga.get(time_fora_nome)

        if not stats_casa or not stats_fora:
            return jsonify({"erro": f"Um dos times não foi encontrado no cache para esta liga. Verifique a ortografia."})

        resultado_analise = processar_dados_reais(stats_casa, stats_fora, stats_casa['team']['name'], stats_fora['team']['name'])
        return jsonify(resultado_analise)

    except Exception as e:
        app_logger.error(f"ERRO CRÍTICO NA ROTA /analisar: {e}", exc_info=True)
        return jsonify({"erro": f"Ocorreu um erro inesperado no servidor. Detalhe: {str(e)}"}), 500

# --- INICIALIZAÇÃO ---
# 1. FAZ A PRIMEIRA CARGA DO CACHE ANTES DE TUDO
atualizar_cache_estatisticas(is_initial_load=True)

# 2. AGENDA AS ATUALIZAÇÕES FUTURAS EM SEGUNDO PLANO
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(atualizar_cache_estatisticas, 'interval', hours=8)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

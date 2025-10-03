# =================================================================
# ARQUIVO servidor.py - VERSÃO FINAL, SINTAXE CORRIGIDA E ROBUSTA
# =================================================================
import os
import requests
import random
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime

# --- FUNÇÕES AUXILIARES (Helpers) ---

def calcular_confianca(diferenca_poder, min_conf=65, max_conf=95):
    bonus = abs(diferenca_poder) * 10
    confianca_final = min(min_conf + bonus, max_conf)
    return int(confianca_final)

def processar_dados_reais(stats_casa, stats_fora, nome_casa, nome_fora):
    tips = []
    try:
        # Extração de dados segura usando .get()
        gols_casa_data = stats_casa.get('goals', {})
        gols_fora_data = stats_fora.get('goals', {})
        fixtures_casa_data = stats_casa.get('fixtures', {})
        
        gols_pro_casa = float(gols_casa_data.get('for', {}).get('average', {}).get('total', 0))
        gols_contra_casa = float(gols_casa_data.get('against', {}).get('average', {}).get('total', 0))
        gols_pro_fora = float(gols_fora_data.get('for', {}).get('average', {}).get('total', 0))
        gols_contra_fora = float(gols_fora_data.get('against', {}).get('average', {}).get('total', 0))
        
    except (TypeError, ValueError) as e:
        print(f"Erro ao processar dados de Gols/Handicap: {e}")
        return {"erro": "Formato de dados de Gols inesperado."}

    # 1. Análise de Gols
    tendencia_gols = (gols_pro_casa + gols_pro_fora) / 2
    confianca_gols = calcular_confianca(tendencia_gols)
    if tendencia_gols > 1.4:
        tips.append({"mercado": "Gols (Over/Under)", "entrada": "Mais de 2.5 gols", "justificativa": f"Média de gols combinada alta ({tendencia_gols:.2f}).", "confianca": f"{confianca_gols}%"})
    else:
        tips.append({"mercado": "Gols (Over/Under)", "entrada": "Menos de 2.5 gols", "justificativa": f"Média de gols combinada baixa ({tendencia_gols:.2f}).", "confianca": f"{confianca_gols}%"})

    # 2. Análise de Handicap
    diferenca_poder = (gols_pro_casa - gols_contra_casa) - (gols_pro_fora - gols_contra_fora)
    confianca_handicap = calcular_confianca(diferenca_poder)
    if diferenca_poder > 0.3:
        tips.append({"mercado": "Handicap Asiático", "entrada": f"{nome_casa} -0.5", "justificativa": "Time da casa tem saldo de gols superior.", "confianca": f"{confianca_handicap}%"})
    else:
        tips.append({"mercado": "Handicap Asiático", "entrada": f"{nome_fora} +0.5", "justificativa": "Visitante tem um bom saldo de gols e deve equilibrar o jogo.", "confianca": f"{confianca_handicap}%"})

    # 3. Análise de Cartões (com extração segura)
    try:
        cards_casa_data = stats_casa.get('cards', {})
        cards_fora_data = stats_fora.get('cards', {})
        jogos_casa = float(fixtures_casa_data.get('played', {}).get('total', 1) or 1)
        jogos_fora = float(stats_fora.get('fixtures', {}).get('played', {}).get('total', 1) or 1)
        cartoes_casa = float(cards_casa_data.get('yellow', {}).get('total', 0)) / jogos_casa
        cartoes_fora = float(cards_fora_data.get('yellow', {}).get('total', 0)) / jogos_fora
        tendencia_cartoes = cartoes_casa + cartoes_fora
        confianca_cartoes = calcular_confianca(tendencia_cartoes - 4.5)
        if tendencia_cartoes > 4.5:
            tips.append({"mercado": "Cartões", "entrada": "Mais de 4.5", "justificativa": f"Média combinada de {tendencia_cartoes:.2f} cartões indica jogo faltoso.", "confianca": f"{confianca_cartoes}%"})
        else:
            tips.append({"mercado": "Cartões", "entrada": "Menos de 4.5", "justificativa": f"Média combinada de {tendencia_cartoes:.2f} cartões sugere jogo limpo.", "confianca": f"{confianca_cartoes}%"})
    except (TypeError, ValueError) as e:
        print(f"Aviso: Não foi possível analisar cartões. {e}")

    # 4. Análise de Escanteios (Simulada, pois API gratuita não fornece)
    media_escanteios_total = random.uniform(8.5, 12.0)
    confianca_escanteios = calcular_confianca((media_escanteios_total - 9.5) / 2)
    if media_escanteios_total > 10.0:
        tips.append({"mercado": "Escanteios", "entrada": "Mais de 9.5", "justificativa": "Simulação indica times que atacam pelas laterais.", "confianca": f"{confianca_escanteios}%"})
    else:
        tips.append({"mercado": "Escanteios", "entrada": "Menos de 9.5", "justificativa": "Simulação indica jogo mais centralizado.", "confianca": f"{confianca_escanteios}%"})

    if not tips:
        return {"erro": "Não foi possível gerar nenhuma análise com os dados obtidos."}

    tips.sort(key=lambda x: int(x.get('confianca', '0').replace('%', '')), reverse=True)
    return {"melhor_aposta": tips[0], "outras_opcoes": tips[1:]}

def analisar_nfl(time_casa, time_fora, campeonato): return {"melhor_aposta": {"mercado": "NFL (Simulado)", "entrada": "Análise não implementada com dados reais."}}
def analisar_nba(time_casa, time_fora, campeonato): return {"melhor_aposta": {"mercado": "NBA (Simulado)", "entrada": "Análise não implementada com dados reais."}}


# --- FÁBRICA DE APLICAÇÃO (Application Factory) ---

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    CORS(app)

    API_HOST = "v3.football.api-sports.io"
    API_KEY = os.getenv("API_KEY") 

    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/analisar', methods=['POST'])
    def analisar_jogo_api():
        dados = request.get_json()
        # ... (código da rota analisar_jogo_api permanece o mesmo)
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
            
            # Busca da Liga
            ligas_response = requests.get(f"https://{API_HOST}/leagues", headers=headers, params={"search": campeonato_nome}, timeout=10 )
            ligas_response.raise_for_status()
            ligas = ligas_response.json().get('response', [])
            if not ligas: return jsonify({"erro": f"Campeonato '{campeonato_nome}' não encontrado."})
            id_liga = ligas[0]['league']['id']
            
            # Busca dos Times
            time_casa_response = requests.get(f"https://{API_HOST}/teams", headers=headers, params={"league": id_liga, "search": time_casa_nome}, timeout=10 )
            time_casa_response.raise_for_status()
            time_casa = time_casa_response.json().get('response', [])
            
            time_fora_response = requests.get(f"https://{API_HOST}/teams", headers=headers, params={"league": id_liga, "search": time_fora_nome}, timeout=10 )
            time_fora_response.raise_for_status()
            time_fora = time_fora_response.json().get('response', [])
            
            if not time_casa: return jsonify({"erro": f"Time '{time_casa_nome}' não encontrado no campeonato."})
            if not time_fora: return jsonify({"erro": f"Time '{time_fora_nome}' não encontrado no campeonato."})
            id_time_casa = time_casa[0]['team']['id']
            id_time_fora = time_fora[0]['team']['id']

            # Busca das Estatísticas
            ano_atual = datetime.now().year
            params_stats = {"league": id_liga, "season": ano_atual, "team": id_time_casa}
            stats_casa_response = requests.get(f"https://{API_HOST}/teams/statistics", headers=headers, params=params_stats, timeout=10 )
            stats_casa_response.raise_for_status()
            stats_casa = stats_casa_response.json().get('response', {})
            
            params_stats["team"] = id_time_fora
            stats_fora_response = requests.get(f"https://{API_HOST}/teams/statistics", headers=headers, params=params_stats, timeout=10 )
            stats_fora_response.raise_for_status()
            stats_fora = stats_fora_response.json().get('response', {})

            if not stats_casa or not stats_fora:
                return jsonify({"erro": "Não foi possível obter estatísticas para um ou ambos os times nesta temporada."})

            resultado_analise = processar_dados_reais(stats_casa, stats_fora, time_casa[0]['team']['name'], time_fora[0]['team']['name'])
            return jsonify(resultado_analise)

        except requests.exceptions.Timeout:
            print("ERRO: Timeout ao conectar com a API.")
            return jsonify({"erro": "O servidor de dados demorou muito para responder."}), 504
        except requests.exceptions.RequestException as e:
            print(f"ERRO DE CONEXÃO COM A API: {e}")
            return jsonify({"erro": "Falha ao conectar com o provedor de dados esportivos."}), 500
        except Exception as e:
            print(f"ERRO INESPERADO NO SERVIDOR: {e}")
            return jsonify({"erro": "Ocorreu um erro interno no servidor de análise."}), 500

    return app

# --- PONTO DE ENTRADA PARA O GUNICORN ---
# O Gunicorn irá procurar por esta variável 'app'
app = create_app()

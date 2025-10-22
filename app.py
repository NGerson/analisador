from flask import Flask, render_template, request, jsonify
import requests
import logging
import random # Necessário para o random.randint em analisar_jogo_com_dados_reais

# --- CONFIGURAÇÕES DA API (Você precisa definir isso) ---
API_BASE_URL = "http://api.football-data.org/v4/" # Exemplo, use a sua URL real
HEADERS = {'X-Auth-Token': 'c246eae154d5464fad88b423dc5d939e'} # Substitua pela sua chave

# A função analisar_jogo_com_dados_reais do seu app.py deve estar aqui ou importada.
# Por simplicidade, vou colocá-la aqui no exemplo:

def analisar_jogo_com_dados_reais(time_casa_nome, time_fora_nome, id_liga):
    # Conteúdo da sua função analisar_jogo_com_dados_reais (copiado do seu app.py)
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
        # As chaves stats_casa e stats_fora agora são dicionários, então acesse com .get
        avg_gols_casa = (stats_casa.get('goalsFor', 0) + stats_fora.get('goalsAgainst', 0)) / 2 / stats_casa.get('playedGames', 1)
        avg_gols_fora = (stats_fora.get('goalsFor', 0) + stats_casa.get('goalsAgainst', 0)) / 2 / stats_fora.get('playedGames', 1)

        tendencia_gols = avg_gols_casa + avg_gols_fora
        
        # Usa a chave 'entrada' como no seu código original
        if tendencia_gols > 2.8:
            tips.append({"mercado": "Gols", "entrada": "Mais de 2.5 gols", "justificativa": f"Tendência de gols alta ({tendencia_gols:.2f}).", "confianca": random.randint(75, 90)})
        else:
            tips.append({"mercado": "Gols", "entrada": "Menos de 2.5 gols", "justificativa": f"Tendência de gols baixa ({tendencia_gols:.2f}).", "confianca": random.randint(70, 85)})

        diferenca_pontos = stats_casa.get('points', 0) - stats_fora.get('points', 0)
        
        # Correção de acesso ao nome do time, usando .get para segurança
        time_casa_nome_completo = stats_casa.get('team', {}).get('name', time_casa_nome)
        time_fora_nome_completo = stats_fora.get('team', {}).get('name', time_fora_nome)

        if diferenca_pontos > 5:
            tips.append({"mercado": "Handicap Asiático", "entrada": f"{time_casa_nome_completo} -0.5", "justificativa": "Time da casa tem campanha muito superior.", "confianca": random.randint(70, 88)})
        elif diferenca_pontos < -5:
            tips.append({"mercado": "Handicap Asiático", "entrada": f"{time_fora_nome_completo} -0.5", "justificativa": "Visitante tem campanha muito superior.", "confianca": random.randint(70, 88)})
        else:
            tips.append({"mercado": "Handicap Asiático", "entrada": f"{time_fora_nome_completo} +0.5", "justificativa": "Jogo equilibrado, visitante tem valor no handicap positivo.", "confianca": random.randint(65, 80)})

        tips.append({"mercado": "Escanteios", "entrada": "Mais de 9.5", "justificativa": "Análise simulada.", "confianca": random.randint(65, 85)})
        tips.append({"mercado": "Cartões", "entrada": "Mais de 4.5", "justificativa": "Análise simulada.", "confianca": random.randint(60, 80)})

        # Ordena usando a confiança como inteiro
        tips.sort(key=lambda x: x['confianca'], reverse=True)
        
        # Prepara o resultado final para o frontend
        resultado_final = {"melhor_aposta": tips[0], "outras_opcoes": tips[1:]}
        
        # Loop para formatar a saída para o frontend
        for tip in [resultado_final['melhor_aposta']] + resultado_final['outras_opcoes']:
            # Renomeia 'entrada' para 'palpite' que o JS espera
            tip['palpite'] = tip.pop('entrada')
            # Converte a confiança de volta para string com '%' que o JS espera
            tip['confianca'] = tip['confianca']
        
        # Nota: O seu JS já adiciona o "%", então deixamos como inteiro/string numérica aqui

        return resultado_final

    except requests.exceptions.RequestException as e:
        logging.error(f"Erro de API: {e}")
        status_code = e.response.status_code if e.response else 500
        if status_code == 403:
             return {"erro": "Acesso negado. Verifique sua chave de API ou plano."}
        return {"erro": f"Erro ao contatar a API de dados: {e}"}
    except Exception as e:
        logging.error(f"Erro inesperado na análise: {e}")
        return {"erro": "Ocorreu um erro interno ao processar a análise."}

# --------------------------------------------------------------------------


app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def home():
    """Rota principal que serve o index.html."""
    return render_template('index.html')

@app.route('/analisar', methods=['POST'])
def analisar():
    """Rota que o JavaScript chama para a análise de dados."""
    data = request.json
    esporte = data.get('esporte')
    mensagem = data.get('mensagem', '').strip()
    
    if esporte == 'futebol':
        if "quero apostar" in mensagem.lower():
            return jsonify({"bot_response": "Qual jogo você quer analisar? Digite no formato: 'Time Casa vs Time Fora (ID da Liga)'. Ex: 'Flamengo vs Fluminense (2016)'"})
        
        # Regex simples para tentar extrair os times e o ID da liga
        try:
            # Espera um formato como: "Time A vs Time B (ID da Liga)"
            partes = mensagem.split('(')
            if len(partes) < 2:
                 return jsonify({"bot_response": "Formato inválido. Use: 'Time Casa vs Time Fora (ID da Liga)'."})
            
            times_str = partes[0].strip()
            liga_id_str = partes[1].replace(')', '').strip()

            times = times_str.split('vs')
            if len(times) != 2:
                return jsonify({"bot_response": "Formato de times inválido. Use: 'Time Casa vs Time Fora'."})

            time_casa = times[0].strip()
            time_fora = times[1].strip()

            try:
                # Na API de exemplo, o ID da liga é um número, então tratamos como tal.
                # Se for um nome (como "2016" para Série A), ajuste o tratamento.
                # Vamos assumir que é o ID numérico 2016 (Brasileirão Série A) por exemplo.
                id_liga = liga_id_str 

            except ValueError:
                return jsonify({"bot_response": "O ID da Liga parece não ser um número válido."})


            # Chama a função de análise real
            resultado_analise = analisar_jogo_com_dados_reais(time_casa, time_fora, id_liga)

            if resultado_analise.get('erro'):
                return jsonify(resultado_analise)
            
            return jsonify(resultado_analise)

        except Exception as e:
            return jsonify({"erro": f"Erro no processamento da entrada: {e}. Tente novamente."})
            
    # Para NFL e NBA, você teria a lógica de análise para esses esportes aqui.
    return jsonify({"bot_response": f"Análise para {esporte.upper()} ainda está em desenvolvimento!"})

if __name__ == '__main__':
    # Você pode definir a porta que quiser, 5000 é a padrão do Flask.
    app.run(debug=True, port=5000)
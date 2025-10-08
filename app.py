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
            return {"erro": f"Um ou ambos os times ('{time_casa_nome}', '{time_fora_nome}') não foram encontrados na classificação. Verifique a ortografia."}

        tips = []
        avg_gols_casa = (stats_casa['goalsFor'] + stats_fora['goalsAgainst']) / 2 / stats_casa['playedGames']
        avg_gols_fora = (stats_fora['goalsFor'] + stats_casa['goalsAgainst']) / 2 / stats_fora['playedGames']
        tendencia_gols = avg_gols_casa + avg_gols_fora
        
        # Usa a chave 'entrada' como no seu código original
        if tendencia_gols > 2.8:
            tips.append({"mercado": "Gols", "entrada": "Mais de 2.5 gols", "justificativa": f"Tendência de gols alta ({tendencia_gols:.2f}).", "confianca": random.randint(75, 90)})
        else:
            tips.append({"mercado": "Gols", "entrada": "Menos de 2.5 gols", "justificativa": f"Tendência de gols baixa ({tendencia_gols:.2f}).", "confianca": random.randint(70, 85)})

        diferenca_pontos = stats_casa['points'] - stats_fora['points']
        if diferenca_pontos > 5:
            tips.append({"mercado": "Handicap Asiático", "entrada": f"{stats_casa['team']['name']} -0.5", "justificativa": "Time da casa tem campanha muito superior.", "confianca": random.randint(70, 88)})
        elif diferenca_pontos < -5:
            tips.append({"mercado": "Handicap Asiático", "entrada": f"{stats_fora['team']['name']} -0.5", "justificativa": "Visitante tem campanha muito superior.", "confianca": random.randint(70, 88)})
        else:
            tips.append({"mercado": "Handicap Asiático", "entrada": f"{stats_fora['team']['name']} +0.5", "justificativa": "Jogo equilibrado, visitante tem valor no handicap positivo.", "confianca": random.randint(65, 80)})

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
            tip['confianca'] = f"{tip['confianca']}%"

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

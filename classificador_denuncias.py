# -*- coding: utf-8 -*-
"""
classificador_denuncias.py
Módulo do SARO - CAO Cidadania responsável pelo carregamento das bases,
classificação via IA Gemini e roteamento de promotorias com base no Município e Atribuição.
"""

import json
import requests
import os
import unicodedata
import streamlit as st
from google import genai
from google.genai import types
from datetime import datetime


class ClassificadorDenuncias:
    def __init__(self):
        # Configuração do Cliente Gemini
        api_key = st.secrets.get("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"
        
        # Webhook do Power Automate (SharePoint)
        self.webhook_url = st.secrets.get("SHAREPOINT_WEBHOOK")
        
        # Caminho e carregamento das bases locais JSON
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega os arquivos de mapeamento temático e territorial do CAO Cidadania."""
        with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
            self.temas_subtemas = json.load(f)
            
        with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
            self.base_promotorias = json.load(f)

    def remover_acentos(self, texto: str) -> str:
        """Remove acentos e caracteres especiais para facilitar buscas em texto."""
        if not texto: 
            return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def buscar_promotoria(self, municipio_informado: str, atribuicao_identificada: str) -> dict:
        """
        Mapeia a Promotoria, Núcleo e Destino com base no Município e na Atribuição definida.
        """
        mun_busca = self.remover_acentos(municipio_informado.strip().upper())
        atrib_busca = self.remover_acentos(atribuicao_identificada.strip().upper())

        for nucleo_nome, promotorias_list in self.base_promotorias.items():
            for item in promotorias_list:
                # Verifica se o município está presente nesta promotoria
                municipios_normalizados = [self.remover_acentos(m.upper()) for m in item["municipios"]]
                
                if mun_busca in municipios_normalizados or any(m in mun_busca for m in municipios_normalizados):
                    # Verifica se a atribuição corresponde
                    atribuicoes_normalizadas = [self.remover_acentos(a.upper()) for a in item["atribuicoes"]]
                    
                    if atrib_busca in atribuicoes_normalizadas or any(a in atrib_busca for a in atribuicoes_normalizadas):
                        return {
                            "nucleo": nucleo_nome,
                            "promotoria": item["promotoria"],
                            "destino": item["destino"]
                        }

        # Fallback caso não ache correspondência exata de atribuição
        for nucleo_nome, promotorias_list in self.base_promotorias.items():
            for item in promotorias_list:
                municipios_normalizados = [self.remover_acentos(m.upper()) for m in item["municipios"]]
                if mun_busca in municipios_normalizados:
                    return {
                        "nucleo": nucleo_nome,
                        "promotoria": item["promotoria"],
                        "destino": item["destino"]
                    }

        return {
            "nucleo": "Não identificado",
            "promotoria": "Não identificada",
            "destino": "Não identificado"
        }

    def processar_denuncia(self, num_com: str, num_mprj: str, data_carga: str, 
                           data_envio: str, municipio: str, quem_enviou: str, 
                           denuncia: str, responsavel: str) -> tuple:
        """
        Processa a denúncia completa: classifica via Gemini IA, busca o endereçamento correto
        e faz o envio dos dados via webhook ao Power Automate / SharePoint.
        """
        
        # 1. Executar Classificação com Inteligência Artificial
        catalogo_temas = json.dumps(self.temas_subtemas, ensure_ascii=False)
        
        prompt = f"""
Você é um assistente de triagem de ouvidorias do Ministério Público do Estado do Rio de Janeiro (MPRJ) - CAO Cidadania.

Analise a seguinte denúncia:
"{denuncia}"

Município Informado: {municipio}

Utilize o catálogo oficial de Temas e Subtemas abaixo:
{catalogo_temas}

Regras:
1. Escolha a ATRIBUIÇÃO adequada entre: ["Patrimônio Público", "Assistência Social", "Direitos Humanos", "Segurança Pública", "Sistema Prisional", "Residual"].
2. Escolha exatamente um TEMA do catálogo.
3. Escolha um SUBTEMA que pertença estritamente ao TEMA escolhido.
4. Defina a CLASSIFICAÇÃO DA OUVIDORIA entre: ["Genérica/Infundada/Incompreensível", "Recorrente", "De Direito Individual", "Outra Atribuição", "Nenhuma das Opções Acima"].
5. Escreva um RESUMO sucinto da denúncia (máximo de 15 palavras).

Retorne ESTRITAMENTE um JSON com as seguintes chaves:
{{
    "atribuicao": "Nome da Atribuição",
    "tema": "Nome do Tema",
    "subtema": "Nome do Subtema",
    "classificacao_ouvidoria": "Nome da Classificação",
    "resumo": "Resumo em poucas palavras"
}}
"""

        configuracao = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )

        try:
            resposta = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=configuracao
            )
            dados_ia = json.loads(resposta.text)
        except Exception as e:
            st.error(f"Erro na análise da IA: {e}")
            dados_ia = {
                "atribuicao": "Residual",
                "tema": "Residual",
                "subtema": "Outros",
                "classificacao_ouvidoria": "Nenhuma das Opções Acima",
                "resumo": "Processamento manual necessário"
            }

        # 2. Identificar Núcleo e Promotoria no Mapeamento
        info_territorial = self.buscar_promotoria(
            municipio_informado=municipio,
            atribuicao_identificada=dados_ia.get("atribuicao", "")
        )

        # 3. Montar o Dicionário Final de Saída
        dados_final = {
            "num_com": num_com,
            "num_mprj": num_mprj,
            "data_carga": data_carga,
            "data_envio": data_envio,
            "municipio": municipio,
            "quem_enviou": quem_enviou,
            "nucleo": info_territorial["nucleo"],
            "atribuicao": dados_ia.get("atribuicao"),
            "promotoria": info_territorial["promotoria"],
            "destino_secretaria": info_territorial["destino"],
            "tema": dados_ia.get("tema"),
            "subtema": dados_ia.get("subtema"),
            "classificacao_ouvidoria": dados_ia.get("classificacao_ouvidoria"),
            "resumo": dados_ia.get("resumo"),
            "denuncia_completa": denuncia,
            "responsavel_triagem": responsavel,
            "data_processamento": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        # 4. Envio dos Dados via Webhook para o SharePoint (Power Automate)
        sucesso = False
        if self.webhook_url:
            try:
                resp = requests.post(self.webhook_url, json=dados_final, timeout=15)
                sucesso = resp.status_code in [200, 202]
            except Exception as e:
                st.error(f"Erro ao conectar com o Power Automate: {e}")

        return dados_final, sucesso

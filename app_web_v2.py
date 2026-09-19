# -*- coding: utf-8 -*-
"""
app_web_v2.py
Interface gráfica interativa em Streamlit para o SARO - CAO Cidadania.
"""

import streamlit as st
import os
from datetime import date
from classificador_denuncias import ClassificadorDenuncias

# Configuração da página web
st.set_page_config(page_title="SARO - CAO Cidadania | MPRJ", layout="wide", page_icon="⚖️")

# Estilização CSS para preservar a identidade visual institucional do MPRJ
st.markdown("""
<style>
    .caixa-resultado {
        border: 1px solid #960018;
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        margin-bottom: 20px;
    }
    .label-vermelho { color: #960018; font-weight: bold; }
    .titulo-custom { color: #960018; font-weight: bold; font-size: 1.5rem; }
    .badge-verde {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: bold;
        display: inline-block;
        margin-right: 10px;
        margin-bottom: 8px;
        border: 1px solid #c8e6c9;
    }
    .resumo-box { background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #960018; }
    .area-planilha { border: 2px solid #960018; padding: 25px; text-align: center; border-radius: 10px; background-color: #ffffff; margin-top: 20px; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Gerenciamento de estado da sessão
if "resultado" not in st.session_state:
    st.session_state.resultado = None

# Inicialização do Classificador de Denúncias
try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro ao iniciar o sistema: {e}")
    st.stop()

# Barra Lateral (Logo Oficial do MPRJ)
st.sidebar.image("https://www.mprj.mp.br/mprj-theme/images/mprj/logo_mprj.png", width=180)

# --- CABEÇALHO PRINCIPAL COM LOGO E TÍTULO LADO A LADO ---
col_logo, col_titulo = st.columns([1, 5])

# --------------------------------------------------------------------------
# 📌 NOME DA IMAGEM ATUALIZADO
NOME_IMAGEM = "CAO CIDADANIA - LOGO 1.png"
# --------------------------------------------------------------------------

diretorio_atual = os.path.dirname(__file__)

# Lógica de verificação do arquivo de imagem
imagem_encontrada = None
extensoes_suportadas = [".png", ".PNG", ".jfif", ".JFIF", ".jpg", ".jpeg", ".JPG", ".JPEG"]

# 1. Verifica se o nome digitado já possui uma extensão válida e se o arquivo existe
caminho_direto = os.path.join(diretorio_atual, NOME_IMAGEM)
if os.path.exists(caminho_direto):
    imagem_encontrada = caminho_direto
else:
    # 2. Se o arquivo direto não for encontrado, tenta remover a extensão e buscar outras variações
    nome_base, _ = os.path.splitext(NOME_IMAGEM)
    for ext in extensoes_suportadas:
        caminho_teste = os.path.join(diretorio_atual, f"{nome_base}{ext}")
        if os.path.exists(caminho_teste):
            imagem_encontrada = caminho_teste
            break

with col_logo:
    if imagem_encontrada:
        st.image(imagem_encontrada, width=130)
    else:
        st.warning(f"⚠️ Imagem '{NOME_IMAGEM}' não encontrada no diretório.")

with col_titulo:
    st.title("⚖️ Sistema Automático de Registro de Ouvidorias (SARO) | CAO Cidadania")
    st.markdown("*Versão 3.0* | Triagem, Gestão e Encaminhamento de Ouvidorias com Inteligência Artificial")

st.divider()

# --- FORMULÁRIO DE REGISTRO ---
with st.form("form_reg", clear_on_submit=True):
    st.markdown('<p class="titulo-custom">📝 Novo Registro de Ouvidoria</p>', unsafe_allow_html=True)
    
    # Linha 1: Números de Identificação
    col1, col2 = st.columns(2)
    num_com = col1.text_input("Nº de Comunicação")
    num_mprj = col2.text_input("Nº MPRJ")
    
    # Linha 2: Datas
    col_d1, col_d2 = st.columns(2)
    data_carga = col_d1.date_input("Data de Carga", value=date.today()).strftime("%d/%m/%Y")
    data_envio = col_d2.date_input("Data de Envio", value=date.today()).strftime("%d/%m/%Y")
    
    # Linha 3: Município e Remetente
    col_m1, col_m2 = st.columns(2)
    municipio = col_m1.text_input("Município do Fato")
    quem_enviou = col_m2.text_input("Quem Enviou (Órgão / Setor / Cidadão)")
    
    # Linha 4: Descrição do Fato
    denuncia = st.text_area("Descrição da Ouvidoria / Denúncia", height=150)
    
    # Linha 5: Responsável pela Triagem
    responsavel = st.radio("Responsável pela Triagem:", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    
    # Botão de Submissão
    if st.form_submit_button("🔍 Registrar e Classificar Ouvidoria", use_container_width=True):
        if municipio and denuncia:
            with st.spinner("Classificando via IA e Integrando ao SharePoint..."):
                res, sucesso = classificador.processar_denuncia(
                    num_com=num_com,
                    num_mprj=num_mprj,
                    data_carga=data_carga,
                    data_envio=data_envio,
                    municipio=municipio,
                    quem_enviou=quem_enviou,
                    denuncia=denuncia,
                    responsavel=responsavel
                )
                st.session_state.resultado = res
                
                if sucesso:
                    st.success("✅ Ouvidoria registrada e enviada com sucesso para o SharePoint!")
                else:
                    st.warning("⚠️ Ouvidoria processada, porém o SharePoint não confirmou o recebimento via Power Automate.")
        else:
            st.error("Por favor, preencha obrigatoriamente o Município e a Descrição da Ouvidoria.")

# --- EXIBIÇÃO DO RESULTADO DA CLASSIFICAÇÃO ---
if st.session_state.resultado:
    res = st.session_state.resultado
    st.divider()
    st.markdown("### ✅ Resultado da Classificação e Encaminhamento")
    
    st.markdown(f"""
    <div class="caixa-resultado">
        <div style="display: flex; justify-content: space-between;">
            <p><span class="label-vermelho">Nº Comunicação:</span> {res['num_com']}</p>
            <p><span class="label-vermelho">Nº MPRJ:</span> {res['num_mprj']}</p>
        </div>
        <hr style="margin: 10px 0;">
        <p>📍 <span class="label-vermelho">Município:</span> {res['municipio']}</p>
        <p>🏢 <span class="label-vermelho">Núcleo:</span> {res['nucleo']}</p>
        <p>⚖️ <span class="label-vermelho">Atribuição:</span> {res['atribuicao']}</p>
        <p>🏛️ <span class="label-vermelho">Promotoria Responsável:</span> {res['promotoria']}</p>
        <p>📬 <span class="label-vermelho">Destino / Secretaria:</span> {res['destino_secretaria']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.markdown(f'<div class="badge-verde">Tema: {res["tema"]}</div>', unsafe_allow_html=True)
    col_t2.markdown(f'<div class="badge-verde">Subtema: {res["subtema"]}</div>', unsafe_allow_html=True)
    col_t3.markdown(f'<div class="badge-verde">Classificação: {res["classificacao_ouvidoria"]}</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Resumo Automático da IA:**")
    st.markdown(f'<div class="resumo-box">{res["resumo"]}</div>', unsafe_allow_html=True)
    
    with st.expander("📄 Ver Descrição Completa da Ouvidoria"):
        st.write(res['denuncia_completa'])
    
    if st.button("Limpar Tela para Novo Registro"):
        st.session_state.resultado = None
        st.rerun()

st.divider()

# --- SEÇÃO DO LINK SHAREPOINT ---
st.markdown('<p class="titulo-custom">📊 Registro de Ouvidorias (SharePoint)</p>', unsafe_allow_html=True)

url_planilha = "https://mprj.sharepoint.com/:x:/r/sites/cao.cidadania.equipe/_layouts/15/Doc.aspx?file=Tabela_SARO_Cidadania.xlsx"

st.markdown(f"""
<div class="area-planilha">
    <p>Acesse a base de dados oficial atualizada em tempo real no SharePoint:</p>
    <a href="{url_planilha}" target="_blank" style="font-weight: bold; color: #960018; font-size: 1.2rem;">
        📂 Abrir Tabela de Ouvidorias (CAO Cidadania)
    </a>
</div>
""", unsafe_allow_html=True)

st.divider()

st.caption("SARO v3.0 - Sistema Automático de Registro de Ouvidorias | CAO Cidadania - Ministério Público do Rio de Janeiro")

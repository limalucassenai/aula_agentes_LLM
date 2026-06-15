"""
Chatbot de Vagas com IA
=======================

Aplicação didática em Streamlit para demonstrar:
- Consumo da API da OpenAI
- Uso de um arquivo XLSX como base de conhecimento simples
- Ranking de vagas por compatibilidade
- Controle de interações por sessão
- Registro de logs locais

Como executar:
    streamlit run app.py
"""

import csv
import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# CONFIGURAÇÕES INICIAIS
# ============================================================

load_dotenv()

st.set_page_config(
    page_title="Chatbot de Vagas com IA",
    page_icon="🤖",
    layout="wide",
)

ARQUIVO_VAGAS = "dados/vagas_simuladas.xlsx"
ARQUIVO_LOGS = "logs/interacoes.csv"
LIMITE_INTERACOES = 8


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================


def criar_pastas_necessarias():
    os.makedirs("dados", exist_ok=True)
    os.makedirs("logs", exist_ok=True)


@st.cache_data
def carregar_vagas(caminho_arquivo: str) -> pd.DataFrame:
    if not os.path.exists(caminho_arquivo):
        st.error(
            f"Arquivo não encontrado: {caminho_arquivo}. "
            "Execute primeiro o arquivo gerar_base_vagas.py."
        )
        st.stop()

    df = pd.read_excel(caminho_arquivo)
    df = df.fillna("")
    return df


def inicializar_estado():
    if "mensagens" not in st.session_state:
        st.session_state.mensagens = []

    if "interacoes" not in st.session_state:
        st.session_state.interacoes = 0

    if "perfil_aluno" not in st.session_state:
        st.session_state.perfil_aluno = {
            "nome": "",
            "area_interesse": "",
            "tecnologias": "",
            "senioridade": "",
            "modalidade": "",
            "cidade": "",
            "estado": "",
        }


def normalizar_texto(texto) -> str:
    return str(texto).lower().strip()


def calcular_pontuacao_vaga(vaga: dict, perfil: dict, pergunta_usuario: str) -> int:
    """
    Ranking simples por palavras-chave.

    A proposta é ser didática. Em uma evolução da aula, os alunos podem substituir
    essa função por embeddings, similaridade de cosseno ou outro algoritmo.
    """

    texto_vaga = " ".join(
        [
            str(vaga.get("cargo", "")),
            str(vaga.get("empresa", "")),
            str(vaga.get("tecnologias", "")),
            str(vaga.get("perfil_desejado", "")),
            str(vaga.get("modalidade", "")),
            str(vaga.get("cidade", "")),
            str(vaga.get("estado", "")),
            str(vaga.get("senioridade", "")),
            str(vaga.get("area", "")),
            str(vaga.get("descricao", "")),
            str(vaga.get("requisitos_obrigatorios", "")),
            str(vaga.get("requisitos_desejaveis", "")),
            str(vaga.get("atividades", "")),
            str(vaga.get("ferramentas", "")),
        ]
    ).lower()

    texto_busca = " ".join(
        [
            perfil.get("area_interesse", ""),
            perfil.get("tecnologias", ""),
            perfil.get("senioridade", ""),
            perfil.get("modalidade", ""),
            perfil.get("cidade", ""),
            perfil.get("estado", ""),
            pergunta_usuario,
        ]
    ).lower()

    termos = [
        termo.strip()
        for termo in texto_busca.replace(",", " ").replace(";", " ").split()
        if len(termo.strip()) > 2
    ]

    pontuacao = 0

    for termo in termos:
        if termo in texto_vaga:
            pontuacao += 1

    modalidade = normalizar_texto(perfil.get("modalidade", ""))
    senioridade = normalizar_texto(perfil.get("senioridade", ""))
    cidade = normalizar_texto(perfil.get("cidade", ""))
    estado = normalizar_texto(perfil.get("estado", ""))

    if modalidade and modalidade in normalizar_texto(vaga.get("modalidade", "")):
        pontuacao += 3

    if senioridade and senioridade in normalizar_texto(vaga.get("senioridade", "")):
        pontuacao += 3

    if cidade and cidade in normalizar_texto(vaga.get("cidade", "")):
        pontuacao += 2

    if estado and estado in normalizar_texto(vaga.get("estado", "")):
        pontuacao += 2

    return pontuacao


def buscar_vagas_compativeis(
    df_vagas: pd.DataFrame,
    perfil: dict,
    pergunta_usuario: str,
    quantidade: int = 5,
) -> list[dict]:
    vagas_com_score = []

    for _, vaga in df_vagas.iterrows():
        vaga_dict = vaga.to_dict()
        score = calcular_pontuacao_vaga(vaga_dict, perfil, pergunta_usuario)
        vaga_dict["score_compatibilidade"] = score
        vagas_com_score.append(vaga_dict)

    vagas_ordenadas = sorted(
        vagas_com_score,
        key=lambda item: item["score_compatibilidade"],
        reverse=True,
    )

    return vagas_ordenadas[:quantidade]


def montar_contexto_vagas(vagas: list[dict]) -> str:
    contexto = []

    for vaga in vagas:
        contexto.append(
            {
                "empresa": vaga.get("empresa", ""),
                "cargo": vaga.get("cargo", ""),
                "data_publicacao": str(vaga.get("data_publicacao", "")),
                "tecnologias": vaga.get("tecnologias", ""),
                "desafios": vaga.get("desafios", ""),
                "perfil_desejado": vaga.get("perfil_desejado", ""),
                "modalidade": vaga.get("modalidade", ""),
                "cidade": vaga.get("cidade", ""),
                "estado": vaga.get("estado", ""),
                "senioridade": vaga.get("senioridade", ""),
                "area": vaga.get("area", ""),
                "tipo_contrato": vaga.get("tipo_contrato", ""),
                "ingles": vaga.get("ingles", ""),
                "salario_estimado": vaga.get("salario_estimado", ""),
                "beneficios": vaga.get("beneficios", ""),
                "requisitos_obrigatorios": vaga.get("requisitos_obrigatorios", ""),
                "requisitos_desejaveis": vaga.get("requisitos_desejaveis", ""),
                "atividades": vaga.get("atividades", ""),
                "ferramentas": vaga.get("ferramentas", ""),
                "descricao": vaga.get("descricao", ""),
                "score_compatibilidade": vaga.get("score_compatibilidade", 0),
            }
        )

    return json.dumps(contexto, ensure_ascii=False, indent=2)


def registrar_log(
    modelo: str,
    perfil: dict,
    pergunta: str,
    resposta: str,
    vagas_recomendadas: list[dict],
):
    criar_pastas_necessarias()

    arquivo_existe = os.path.exists(ARQUIVO_LOGS)

    with open(ARQUIVO_LOGS, mode="a", newline="", encoding="utf-8") as arquivo:
        campos = [
            "data_hora",
            "modelo",
            "nome_usuario",
            "area_interesse",
            "tecnologias",
            "pergunta",
            "resposta",
            "vagas_recomendadas",
        ]

        writer = csv.DictWriter(arquivo, fieldnames=campos)

        if not arquivo_existe:
            writer.writeheader()

        writer.writerow(
            {
                "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "modelo": modelo,
                "nome_usuario": perfil.get("nome", ""),
                "area_interesse": perfil.get("area_interesse", ""),
                "tecnologias": perfil.get("tecnologias", ""),
                "pergunta": pergunta,
                "resposta": resposta,
                "vagas_recomendadas": json.dumps(vagas_recomendadas, ensure_ascii=False, default=str),
            }
        )


def gerar_resposta_openai(
    api_key: str,
    modelo: str,
    perfil: dict,
    pergunta_usuario: str,
    contexto_vagas: str,
) -> str:
    client = OpenAI(api_key=api_key)

    prompt_sistema = f"""
Você é um assistente de orientação profissional para alunos de tecnologia.

Sua função é:
1. Analisar o perfil informado pelo aluno.
2. Usar APENAS as vagas fornecidas no contexto.
3. Recomendar as vagas mais compatíveis.
4. Explicar de forma clara o motivo da recomendação.
5. Sugerir conhecimentos que o aluno deveria estudar para melhorar a aderência.
6. Não inventar vagas que não estejam no contexto.
7. Responder em português do Brasil, de forma objetiva e didática.

Perfil do aluno:
- Nome: {perfil.get("nome", "")}
- Área de interesse: {perfil.get("area_interesse", "")}
- Tecnologias conhecidas: {perfil.get("tecnologias", "")}
- Senioridade desejada: {perfil.get("senioridade", "")}
- Modalidade desejada: {perfil.get("modalidade", "")}
- Cidade: {perfil.get("cidade", "")}
- Estado: {perfil.get("estado", "")}

Vagas disponíveis em formato JSON:
{contexto_vagas}
"""

    resposta = client.responses.create(
        model=modelo,
        input=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": pergunta_usuario},
        ],
    )

    return resposta.output_text


# ============================================================
# APLICAÇÃO STREAMLIT
# ============================================================

criar_pastas_necessarias()
inicializar_estado()

df_vagas = carregar_vagas(ARQUIVO_VAGAS)

st.title("🤖 Chatbot de Vagas com IA")
st.write(
    "Este app usa uma base XLSX de vagas, coleta o perfil do usuário e utiliza "
    "a API da OpenAI para recomendar oportunidades compatíveis."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Configurações")

    api_key_env = os.getenv("OPENAI_API_KEY", "")

    usar_chave_env = st.checkbox(
        "Usar API key do arquivo .env",
        value=True,
    )

    if usar_chave_env:
        api_key = api_key_env
        if api_key:
            st.success("API key carregada do .env")
        else:
            st.warning("Nenhuma API key encontrada no .env")
    else:
        api_key = st.text_input(
            "Digite sua API key",
            type="password",
        )

    modelo = st.selectbox(
        "Escolha o modelo",
        [
            "gpt-4.1-mini",
            "gpt-4o-mini",
            "gpt-5.4-mini",
        ],
        index=0,
    )

    st.caption(
        "Caso um modelo não esteja disponível na sua conta, selecione outro modelo da lista."
    )

    st.divider()

    st.header("👤 Perfil do aluno")

    st.session_state.perfil_aluno["nome"] = st.text_input(
        "Nome",
        value=st.session_state.perfil_aluno["nome"],
    )

    st.session_state.perfil_aluno["area_interesse"] = st.text_input(
        "Área de interesse",
        value=st.session_state.perfil_aluno["area_interesse"],
        placeholder="Ex: Dados, IA, Desenvolvimento, RPA",
    )

    st.session_state.perfil_aluno["tecnologias"] = st.text_area(
        "Tecnologias que conhece",
        value=st.session_state.perfil_aluno["tecnologias"],
        placeholder="Ex: Python, SQL, Power BI, Selenium",
    )

    st.session_state.perfil_aluno["senioridade"] = st.selectbox(
        "Senioridade desejada",
        ["", "Júnior", "Pleno", "Sênior"],
        index=0,
    )

    st.session_state.perfil_aluno["modalidade"] = st.selectbox(
        "Modalidade desejada",
        ["", "Remoto", "Híbrido", "Presencial"],
        index=0,
    )

    st.session_state.perfil_aluno["cidade"] = st.text_input(
        "Cidade",
        value=st.session_state.perfil_aluno["cidade"],
        placeholder="Ex: Joinville",
    )

    st.session_state.perfil_aluno["estado"] = st.text_input(
        "Estado",
        value=st.session_state.perfil_aluno["estado"],
        placeholder="Ex: SC",
    )

    st.divider()

    st.metric(
        "Interações usadas",
        f"{st.session_state.interacoes}/{LIMITE_INTERACOES}",
    )

    if st.button("Limpar conversa"):
        st.session_state.mensagens = []
        st.session_state.interacoes = 0
        st.rerun()


# ============================================================
# VISUALIZAÇÃO DA BASE
# ============================================================

with st.expander("📊 Ver base de vagas carregada"):
    st.dataframe(df_vagas, use_container_width=True)

with st.expander("🧪 Sugestões de perguntas para testar"):
    st.markdown(
        """
- Quais vagas combinam com meu perfil?
- Tenho Python e SQL. Qual vaga você recomenda?
- Quero trabalhar remoto com inteligência artificial. Quais opções fazem sentido?
- Estou começando em RPA. Qual vaga é mais adequada?
- Quais tecnologias devo estudar para melhorar minha aderência?
"""
    )


# ============================================================
# HISTÓRICO DO CHAT
# ============================================================

for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])


# ============================================================
# ENTRADA DO USUÁRIO
# ============================================================

if st.session_state.interacoes >= LIMITE_INTERACOES:
    st.warning(
        "Limite de interações atingido nesta sessão. "
        "Clique em 'Limpar conversa' para reiniciar."
    )
else:
    pergunta_usuario = st.chat_input(
        "Digite sua pergunta. Ex: Quais vagas combinam com meu perfil?"
    )

    if pergunta_usuario:
        if not api_key:
            st.error("Informe uma API key antes de enviar mensagens.")
            st.stop()

        st.session_state.mensagens.append(
            {"role": "user", "content": pergunta_usuario}
        )

        with st.chat_message("user"):
            st.markdown(pergunta_usuario)

        with st.chat_message("assistant"):
            with st.spinner("Analisando vagas compatíveis..."):
                try:
                    perfil = st.session_state.perfil_aluno

                    vagas_recomendadas = buscar_vagas_compativeis(
                        df_vagas=df_vagas,
                        perfil=perfil,
                        pergunta_usuario=pergunta_usuario,
                        quantidade=5,
                    )

                    contexto_vagas = montar_contexto_vagas(vagas_recomendadas)

                    resposta = gerar_resposta_openai(
                        api_key=api_key,
                        modelo=modelo,
                        perfil=perfil,
                        pergunta_usuario=pergunta_usuario,
                        contexto_vagas=contexto_vagas,
                    )

                    st.markdown(resposta)

                    st.session_state.mensagens.append(
                        {"role": "assistant", "content": resposta}
                    )

                    st.session_state.interacoes += 1

                    registrar_log(
                        modelo=modelo,
                        perfil=perfil,
                        pergunta=pergunta_usuario,
                        resposta=resposta,
                        vagas_recomendadas=vagas_recomendadas,
                    )

                except Exception as erro:
                    st.error("Ocorreu um erro ao chamar a API ou processar a resposta.")
                    st.exception(erro)

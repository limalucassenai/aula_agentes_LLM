# Chatbot de Vagas com IA

Projeto didático em Python + Streamlit para demonstrar o uso de APIs de IA com uma base própria de dados em XLSX.

## Objetivo da aula

Este projeto pode ser usado em dois momentos:

1. **Consumo de API de IA**
   - Autenticação com API key.
   - Envio de prompts para um modelo da OpenAI.
   - Exibição da resposta em formato de chat.

2. **Chatbot com base de dados própria**
   - Leitura de um arquivo XLSX com vagas simuladas.
   - Coleta do perfil do aluno.
   - Ranking simples das vagas mais compatíveis.
   - Uso da IA para explicar as recomendações.
   - Controle de limite de interações e registro de logs.

## Estrutura do projeto

```text
chatbot_vagas_ia/
│
├── app.py
├── gerar_base_vagas.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── dados/
│   └── vagas_simuladas.xlsx
│
└── logs/
    └── .gitkeep
```

## Como rodar no VS Code

### 1. Criar ambiente virtual

```bash
python -m venv .venv
```

### 2. Ativar ambiente virtual

No Windows:

```bash
.venv\Scripts\activate
```

No Linux/Mac:

```bash
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar a chave da OpenAI

Copie o arquivo `.env.example` e renomeie para `.env`.

Depois, edite o conteúdo:

```env
OPENAI_API_KEY=sua_chave_aqui
```

Também é possível desmarcar a opção de uso do `.env` dentro do app e digitar a chave diretamente na interface.

### 5. Rodar o app

```bash
streamlit run app.py
```

## Como regenerar a base de vagas

O arquivo `dados/vagas_simuladas.xlsx` já está incluído no projeto.

Caso queira recriá-lo:

```bash
python gerar_base_vagas.py
```

## Sugestões de perguntas para teste

- Quais vagas combinam com meu perfil?
- Tenho Python e SQL. Qual vaga você recomenda?
- Quero trabalhar remoto com inteligência artificial. Quais opções fazem sentido?
- Estou começando em RPA. Qual vaga é mais adequada?
- Quais tecnologias devo estudar para melhorar minha aderência?

## Pontos para discussão em sala

- Diferença entre chatbot genérico e chatbot com base própria.
- O que é contexto enviado para o modelo.
- Como funciona uma API key.
- Por que controlar o número de chamadas à API.
- Para que servem logs em aplicações com IA.
- Limitações de um ranking simples por palavras-chave.
- Possíveis evoluções: embeddings, RAG, banco vetorial, agentes com ferramentas e Agno.

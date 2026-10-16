# RAG + Bruno Gabriel Nunes

Projeto didático e funcional de **Retrieval-Augmented Generation (RAG)** focado na ingestão, estruturação e consulta vetorial de Notas Fiscais em PDF.

---

## 🎨 Identidade Visual e Arquitetura

- **Nome do Projeto**: `RAG + Bruno Gabriel Nunes`
- **Tema Visual**: Vermelho Vinho (`#722F37`, `#581825`) com detalhes em Dourado/Amarelo (`#F59E0B`, `#FCD34D`).
- **Frontend**: HTML5, Vanilla CSS, JavaScript (sem frameworks pesados no client-side).
- **Backend**: Python 3.14 + FastAPI + Uvicorn.
- **Embeddings**: **FastEmbed** (`BAAI/bge-small-en-v1.5`, vetor de dimensão **384d**).
- **Banco Vetorial**: **Supabase** (PostgreSQL + PGVECTOR).
- **LLM**: **OpenRouter API** (`openrouter/auto`).

---

## 🚀 Como Executar o Projeto

### 1. Pré-requisitos e Ambiente Virtual

Certifique-se de ter o Python 3.10+ instalado. O ambiente virtual `.venv` já está configurado.

Para ativar o ambiente virtual:

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Configuração de Variáveis de Ambiente (`.env`)

Crie ou edite o arquivo `.env` na raiz do projeto com as suas credenciais:

```env
SUPABASE_URL=https://sua-url-do-supabase.supabase.co
SUPABASE_SECRET_KEY=sua-chave-secret-ou-service-role
OPENROUTER_API_KEY=sk-or-v1-sua-chave-openrouter
OPENROUTER_MODEL=openrouter/auto
```

> ⚠️ **Segurança**: Nunca versione o arquivo `.env`. O arquivo `.gitignore` já está configurado para proteger dados sensíveis.

### 3. Gerar Documentos Fictícios de Exemplo

Para criar as 4 notas fiscais fictícias em formato PDF (`NF_001.pdf` a `NF_004.pdf`):

```bash
python scripts/generate_invoices.py
```

### 4. Teste de Conectividade do Supabase

Antes de iniciar a aplicação web, valide a comunicação com o Supabase:

```bash
python tests/test_supabase.py
```

### 5. Iniciar o Servidor Web Backend

Execute o servidor Uvicorn:

```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Acesse a interface no navegador: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 📊 Fluxo Didático da Aplicação

### Aba Ingestão
Mostra visualmente a esteira de processamento:
$$\text{INGESTÃO} \longrightarrow \text{TOKENIZAÇÃO} \longrightarrow \text{EMBEDDING} \longrightarrow \text{ÍNDICE VETORIAL}$$
- Leitura de PDFs por OCR/Extrator.
- Estruturação dos dados tabulares locais (Nota, Data, Emitente, Destinatário, Produtos, Valores).
- Gravação persistente dos arquivos PDF no **Supabase Storage** (bucket `documents`).
- Geração de Embeddings com FastEmbed e gravação no Supabase PGVECTOR (tabela `documents`).

### Aba Consulta (Chat RAG)
Mostra didaticamente o fluxo de busca e resposta:
$$\text{PERGUNTA} \rightarrow \text{TOKENIZAÇÃO} \rightarrow \text{EMBEDDING} \rightarrow \text{RETRIEVAL} \rightarrow \text{PROMPT AUMENTADO} \rightarrow \text{LLM}$$
- Busca pelos **Top 5 candidatos** com scores de similaridade de cosseno real.
- Visualização do **Prompt Aumentado** (Contexto + Pergunta).
- **Regra de Ausência de Dados**: Caso a pergunta esteja fora do escopo da base ou não existam candidatos relevantes, o sistema retorna exatamente: `"Sem dados disponíveis na base"`.

---

## 📂 Estrutura de Arquivos Organizada (Boas Práticas)

```
rag_java/
├── .env                       # Credenciais e variáveis de ambiente (ignorado no git)
├── .gitignore                 # Proteção de dados e pastas virtuais
├── requirements.txt           # Dependências do projeto Python
├── app.py                     # Entry point da aplicação FastAPI e rotas REST
│
├── src/                       # Código-fonte principal modularizado
│   ├── core/                  # Módulos centrais do sistema
│   │   ├── config.py          # Configurações e leitura do .env
│   │   └── database.py        # Integração Supabase (DB PostgREST + Storage + Cache)
│   └── services/              # Camada de serviços de negócio
│       ├── embedding_service.py # FastEmbed (BAAI/bge-small-en-v1.5, 384d)
│       ├── ocr_ingestion.py     # Pipeline OCR, chunking e envio ao Supabase
│       └── rag_service.py       # Orquestração do RAG e consulta OpenRouter
│
├── documents/                 # PDFs gerados para processamento
│
├── scripts/                   # Scripts utilitários de suporte
│   └── generate_invoices.py   # Gerador de notas fiscais fictícias em PDF
│
├── tests/                     # Testes automatizados e de conectividade
│   ├── test_supabase.py       # Validação da conexão com Supabase API
│   └── test_full_pipeline.py  # Teste E2E do pipeline completo RAG
│
├── docs/                      # Documentações e relatórios de projeto
│   ├── prompt.txt             # Especificação e prompts do sistema
│   ├── ambiente_stacks.txt    # Detalhes do ambiente e stacks
│   └── relatorio_execucao_validacao.md # Relatório de validação
│
└── static/                    # Frontend da aplicação web
    ├── index.html             # Interface principal (Dual Tab: Ingestão e Consulta)
    ├── pipeline.html          # Visualização didática interativa de esteiras
    ├── styles.css             # Design System (Vinho escuro e Dourado)
    └── app.js                 # Lógica de interação client-side
```

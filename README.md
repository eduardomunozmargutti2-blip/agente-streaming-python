# agente-streaming-python

PoC de API REST com streaming de respostas da OpenAI usando FastAPI.

O endpoint `POST /chat` chama o modelo com `stream=True` e devolve os tokens ao cliente via
`StreamingResponse` (chunked transfer encoding), sem esperar a resposta completa.

## Requisitos

- Python 3.10+
- Chave da OpenAI (`OPENAI_API_KEY`)

## Instalação

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (Git Bash)
source .venv/Scripts/activate

# Windows (CMD / PowerShell)
.venv\Scripts\activate

pip install -r requirements.txt
```

## Configuração

```bash
cp .env.example .env
# edite .env e informe sua OPENAI_API_KEY
```

Também é possível exportar a variável direto no terminal:

```bash
export OPENAI_API_KEY="sk-proj-sua_chave_aqui"
```

O modelo é configurável via `OPENAI_MODEL` (padrão: `gpt-4o-mini`).

## Execução

```bash
uvicorn main:app --reload
```

Servidor em `http://127.0.0.1:8000`.

## Endpoints

| Método | Rota      | Descrição                                              |
| ------ | --------- | ------------------------------------------------------ |
| GET    | `/`       | Interface web mínima para testar o streaming            |
| POST   | `/chat`   | Recebe `{"prompt": "..."}` e responde em streaming      |
| GET    | `/health` | Status do serviço, modelo e se a API key está definida  |

## Teste via cURL

```bash
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Escreva um poema de 4 linhas sobre código Python."}'
```

A flag `-N` desabilita o buffer do cURL, permitindo ver os tokens chegando em tempo real.

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

Os testes usam um cliente OpenAI falso, portanto não consomem créditos nem exigem chave real.

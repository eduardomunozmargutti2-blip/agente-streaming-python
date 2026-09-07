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
| POST   | `/chat/sse` | Mesmo streaming em formato Server-Sent Events         |
| GET    | `/health` | Status do serviço, modelo e se a API key está definida  |

## Teste via cURL

```bash
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Escreva um poema de 4 linhas sobre codigo Python."}'
```

A flag `-N` desabilita o buffer do cURL, permitindo ver os tokens chegando em tempo real.

## Como confirmar que o streaming está funcionando

- **cURL com `-N`** ou a página em `/`: o texto aparece progressivamente, em vez de tudo de uma vez.
- **Headers da resposta**: `Transfer-Encoding: chunked` e ausência de `Content-Length` indicam resposta fragmentada.
- **Postman**: ele só exibe a resposta chunk a chunk quando o tipo é `text/event-stream`. Use
  `POST /chat/sse` para ver os eventos chegando em tempo real na aba de resposta; em `POST /chat`
  (`text/plain`) o Postman aguarda o fim e mostra apenas o texto completo.

```bash
curl -N -X POST http://localhost:8000/chat/sse \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Conte de 1 a 10."}'
```

## Troubleshooting

**`400 {"detail":"There was an error parsing the body"}` no Windows (Git Bash/CMD):** o terminal envia
o corpo em cp1252 e o servidor espera UTF-8. Envie o JSON a partir de um arquivo salvo em UTF-8:

```bash
printf '{"prompt": "Escreva um poema de 4 linhas sobre codigo Python."}' > body.json
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  --data-binary @body.json
```

Alternativamente, escreva o prompt sem acentos ou use a interface web em `/`, que sempre envia UTF-8.

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

Os testes usam um cliente OpenAI falso, portanto não consomem créditos nem exigem chave real.

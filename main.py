import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="PoC OpenAI Streaming REST API")


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1)


def get_client() -> AsyncOpenAI:
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY não encontrada nas variáveis de ambiente.",
        )
    return AsyncOpenAI()


async def generate_openai_stream(prompt: str):
    """Consome a API da OpenAI em modo streaming e emite os trechos de texto."""
    client = get_client()
    try:
        stream = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as exc:  # noqa: BLE001 - erro precisa chegar ao cliente já conectado
        yield f"\n[Erro na geração OpenAI: {exc}]"


@app.post("/chat")
async def chat_endpoint(payload: ChatRequest):
    """Recebe um prompt em JSON e devolve a resposta em streaming (text/plain)."""
    get_client()
    return StreamingResponse(
        generate_openai_stream(payload.prompt),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def generate_sse_stream(prompt: str):
    """Mesmo stream em formato Server-Sent Events, visível chunk a chunk no Postman."""
    async for content in generate_openai_stream(prompt):
        yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"


@app.post("/chat/sse")
async def chat_sse_endpoint(payload: ChatRequest):
    """Variante SSE do /chat, para clientes que exibem streaming apenas em text/event-stream."""
    get_client()
    return StreamingResponse(
        generate_sse_stream(payload.prompt),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL, "api_key_configured": bool(os.getenv("OPENAI_API_KEY"))}


@app.get("/")
async def interface_teste():
    return FileResponse(STATIC_DIR / "index.html")

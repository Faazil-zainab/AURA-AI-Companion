"""HTTP chat endpoint for local llama.cpp inference."""

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import ChatRequest, ChatResponse
from app.services.llm_service import (
    LLMResponseError,
    LLMService,
    LLMUnavailableError,
)


router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    """Generate a response from the configured local model server."""

    service: LLMService = request.app.state.llm_service
    try:
        messages = service.build_messages(payload.message, payload.history)
        reply = await service.generate(messages)
    except LLMUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": str(exc),
                "request_id": request.state.request_id,
            },
        ) from exc
    except LLMResponseError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": str(exc),
                "request_id": request.state.request_id,
            },
        ) from exc

    return ChatResponse(
        session_id=payload.session_id,
        reply=reply,
        request_id=request.state.request_id,
    )

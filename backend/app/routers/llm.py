"""LLM compatibility endpoints - OpenAI-compatible /chat/completions for Vapi/Retell."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import logging

from app.agents.dispatch import OrchestratorDispatch
from app.auth.middleware import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["llm"])


class Message(BaseModel):
    role: str  # user, assistant, system
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "claude-opus-5-5"
    messages: List[Message]
    temperature: float = 0.7
    max_tokens: int = 2000
    stream: bool = False


class ChatCompletionChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    id: str = "chatcmpl-demo"
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: dict


@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    current_user = Depends(verify_token)
):
    """
    OpenAI-compatible /chat/completions endpoint.

    This allows Vapi, Retell, or other voice platforms to use
    the Orchestrator as a custom LLM.

    Example:
    ```
    POST /v1/chat/completions
    {
        "model": "claude-opus-5-5",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's my pipeline status?"}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    ```

    Returns:
    ```
    {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "You have 30 leads in pipeline..."
            }
        }]
    }
    ```
    """

    try:
        org_id = current_user.org_id
        user_id = current_user.id

        # Extract user message (last message with role=user)
        user_message = ""
        system_message = ""

        for msg in reversed(request.messages):
            if msg.role == "user" and not user_message:
                user_message = msg.content
            if msg.role == "system" and not system_message:
                system_message = msg.content

        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")

        # Dispatch through orchestrator
        dispatcher = OrchestratorDispatch(org_id, user_id)

        # For voice, use fast tier (Haiku routing)
        result = await dispatcher.handle_user_message(
            message=user_message,
            conversation_id=None  # Create new conversation
        )

        response_text = result.get("response", "I'm not sure how to help with that.")

        # Return OpenAI-compatible response
        from datetime import datetime

        return ChatCompletionResponse(
            model=request.model,
            created=int(datetime.utcnow().timestamp()),
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=Message(
                        role="assistant",
                        content=response_text
                    )
                )
            ],
            usage={
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(user_message.split()) + len(response_text.split())
            }
        )

    except Exception as e:
        logger.error(f"Chat completion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/completions/stream")
async def chat_completions_stream(
    request: ChatCompletionRequest,
    current_user = Depends(verify_token)
):
    """
    Streaming version for real-time voice.

    Returns Server-Sent Events (SSE) stream.
    """

    import asyncio
    from fastapi.responses import StreamingResponse

    async def event_generator():
        try:
            org_id = current_user.org_id
            user_id = current_user.id

            # Extract user message
            user_message = ""
            for msg in reversed(request.messages):
                if msg.role == "user" and not user_message:
                    user_message = msg.content

            if not user_message:
                yield f"data: {json.dumps({'error': 'No user message'})}\n\n"
                return

            # Dispatch
            dispatcher = OrchestratorDispatch(org_id, user_id)
            result = await dispatcher.handle_user_message(
                message=user_message,
                conversation_id=None
            )

            response_text = result.get("response", "")

            # Stream response character by character
            from datetime import datetime
            for i, chunk in enumerate(response_text.split()):
                event = {
                    "choices": [{
                        "delta": {"content": chunk + " "},
                        "index": 0,
                        "finish_reason": None if i < len(response_text.split()) - 1 else "stop"
                    }]
                }
                yield f"data: {json.dumps(event)}\n\n"
                await asyncio.sleep(0.05)  # Simulate streaming

            # Final message
            yield f"data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Stream failed: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

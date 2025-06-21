from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.database.models import ChatBot, Dialogue, DialogueMessage, MessageRole
from core.schemas import WebhookRequest
from predict.mock_llm_call import mock_llm_call
import httpx

router = APIRouter(tags=["Webhooks"])
bearer_scheme = HTTPBearer(auto_error=True)


@router.post("/webhook/new_message", summary="Handle Webhook")
async def handle_webhook(
    message: WebhookRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Handle incoming webhook message — following existing async pattern.
    """
    token = credentials.credentials

    chatbot = await ChatBot.find_one(ChatBot.secret_token == token)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    dialogue = await Dialogue.find_one(
        Dialogue.chat_bot_id == chatbot.id,
        Dialogue.chat_id == message.chat_id,
    )
    if not dialogue:
        dialogue = Dialogue(
            chat_bot_id=chatbot.id,
            chat_id=message.chat_id,
            message_list=[],
            processed_message_ids=[],
        )
        await dialogue.insert()

    if message.message_id in dialogue.processed_message_ids:
        return {"status": "already_processed"}

    if message.message_sender == "employee":
        dialogue.processed_message_ids.append(message.message_id)
        await dialogue.save()
        return {"status": "employee_message_ignored"}

    user_message = DialogueMessage(
        role=MessageRole.USER,
        text=message.text,
        message_id=message.message_id,
    )
    chat_history = dialogue.message_list + [user_message]

    response_text = await mock_llm_call(chat_history)
    assistant_message = DialogueMessage(
        role=MessageRole.ASSISTANT,
        text=response_text,
    )

    dialogue.message_list.extend([user_message, assistant_message])
    dialogue.processed_message_ids.append(message.message_id)
    await dialogue.save()

    await send_message_to_channel(chatbot, message.chat_id, response_text)

    return {"status": "processed", "response": response_text}


async def send_message_to_channel(chatbot: ChatBot, chat_id: str, text: str) -> bool:
    """Send message to external channel via HTTP POST."""
    payload = {"event_type": "new_message", "chat_id": chat_id, "text": text}
    headers = {
        "Authorization": f"Bearer {chatbot.channel_token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                chatbot.channel_url,
                json=payload,
                headers=headers,
                timeout=10.0,
            )
            return response.status_code == 200
        except Exception:
            return False

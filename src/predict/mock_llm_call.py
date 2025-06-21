from asyncio import sleep
from random import randint
import secrets

from core.database.models import DialogueMessage


async def mock_llm_call(chat_history: list[DialogueMessage]) -> str:
    await sleep(randint(1, 5))
    return "New message from llm"


def generate_token() -> str:
    """Generate secure token for chatbot authentication"""
    return secrets.token_urlsafe(32)

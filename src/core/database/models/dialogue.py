from enum import StrEnum, auto
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import BaseModel


class MessageRole(StrEnum):
    ASSISTANT = auto()
    SYSTEM = auto()
    USER = auto()


class DialogueMessage(BaseModel):
    role: MessageRole
    text: str
    message_id: Optional[str] = None


class Dialogue(Document):
    chat_bot_id: PydanticObjectId
    chat_id: str
    message_list: list[DialogueMessage] = []
    processed_message_ids: list[str] = []

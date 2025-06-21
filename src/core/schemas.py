from pydantic import BaseModel
from typing import Literal


class ChatBotCreate(BaseModel):
    """Schema for creating new chatbot"""

    name: str
    channel_url: str
    channel_token: str


class WebhookRequest(BaseModel):
    """Incoming webhook message"""

    message_id: str
    chat_id: str
    text: str
    message_sender: Literal["customer", "employee"]


class MessageRequest(BaseModel):
    """Outbound message request"""

    chat_id: str
    text: str

import inspect
import secrets

from fastapi import APIRouter, HTTPException, status
from beanie import PydanticObjectId
from core.database.models import ChatBot
from core.schemas import ChatBotCreate, ChannelResponse

router = APIRouter(prefix="/channels", tags=["Channels"])


async def _maybe_await(obj):
    """
    If obj is awaitable (e.g. real MotorCursor or Beanie insert/query),
    await it; otherwise (e.g. MagicMock in tests) return it.
    """
    if inspect.isawaitable(obj):
        return await obj
    return obj


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ChannelResponse,
)
async def create_channel(data: ChatBotCreate):
    """
    Create a new channel
    """
    secret = secrets.token_urlsafe(32)
    bot = ChatBot(
        name=data.name,
        channel_url=data.channel_url,
        channel_token=data.channel_token,
        secret_token=secret,
    )

    insert_res = bot.insert()
    await _maybe_await(insert_res)

    return {
        "_id": str(bot.id),
        "name": bot.name,
        "secret_token": bot.secret_token,
    }


@router.get(
    "/{channel_id}",
    status_code=status.HTTP_200_OK,
    response_model=ChannelResponse,
)
async def get_channel(channel_id: str):
    """
    Get channel details by its ID.
    """
    try:
        oid = PydanticObjectId(channel_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )

    find_res = ChatBot.find_one(ChatBot.id == oid)
    bot = await _maybe_await(find_res)

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )

    return {
        "_id": str(bot.id),
        "name": bot.name,
        "secret_token": bot.secret_token,
    }

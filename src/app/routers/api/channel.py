from fastapi import APIRouter, HTTPException
from core.database.models import ChatBot
from core.schemas import ChatBotCreate
from predict.mock_llm_call import generate_token

router = APIRouter(tags=["Channels"])


@router.post("/channels", response_model=ChatBot)
async def create_channel(channel_data: ChatBotCreate):
    """Create new chatbot"""

    secret = generate_token()

    bot = ChatBot(
        name=channel_data.name,
        channel_url=channel_data.channel_url,
        channel_token=channel_data.channel_token,
        secret_token=secret,
    )
    await bot.insert()
    return bot


@router.get("/channels", response_model=list[ChatBot])
async def list_channels():
    """List all chatbots"""

    return await ChatBot.find_all().to_list()


@router.get("/channels/{channel_id}", response_model=ChatBot)
async def get_channel(channel_id: str):
    """Get specific chatbot"""

    bot = await ChatBot.get(channel_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Channel not found")
    return bot


@router.put("/channels/{channel_id}", response_model=ChatBot)
async def update_channel(channel_id: str, channel_data: ChatBotCreate):
    """Update chatbot configuration"""

    bot = await ChatBot.get(channel_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Channel not found")

    bot.name = channel_data.name
    bot.channel_url = channel_data.channel_url
    bot.channel_token = channel_data.channel_token
    await bot.save()
    return bot


@router.delete("/channels/{channel_id}")
async def delete_channel(channel_id: str):
    """Delete chatbot"""

    bot = await ChatBot.get(channel_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Channel not found")
    await bot.delete()
    return {"status": "deleted"}

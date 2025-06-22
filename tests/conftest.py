import asyncio
import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
import secrets

import pytest
from httpx import ASGITransport, AsyncClient
from src.app.app import app


os.environ["MONGO__URL"] = "mongodb://localhost:27017"
os.environ["MONGO__DB_NAME"] = "chatbot_test"


_mock_database = {"chatbots": {}, "dialogues": {}}


def clear_mock_database():
    """Clear all mock data between tests."""
    _mock_database["chatbots"].clear()
    _mock_database["dialogues"].clear()


def generate_test_id():
    """Generate a test ID that looks like MongoDB ObjectId."""
    return str(ObjectId())


@pytest.fixture(scope="session")
def event_loop():
    """Event loop fixture for session scope."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="session")
async def init_db():
    """Mock database initialization."""
    with patch(
        "core.database.registry.initialize_database", new_callable=AsyncMock
    ) as mock_init:
        mock_init.return_value = None
        with patch("beanie.init_beanie", new_callable=AsyncMock) as mock_beanie_init:
            mock_beanie_init.return_value = None
            yield


@pytest.fixture(autouse=True, scope="function")
async def mock_database_operations(mocker):
    """Simple database mocking for tests."""
    clear_mock_database()

    def mock_chatbot_constructor(**kwargs):
        """Create a simple mock ChatBot."""
        mock_bot = MagicMock()
        mock_bot.name = kwargs.get("name", "Test Channel")
        mock_bot.channel_url = kwargs.get("channel_url", "https://example.com")
        mock_bot.channel_token = kwargs.get("channel_token", "token123")
        mock_bot.secret_token = kwargs.get("secret_token", secrets.token_urlsafe(16))
        mock_bot.id = ObjectId()

        async def mock_insert():
            bot_id = str(mock_bot.id)
            _mock_database["chatbots"][bot_id] = {
                "_id": bot_id,
                "name": mock_bot.name,
                "channel_url": mock_bot.channel_url,
                "channel_token": mock_bot.channel_token,
                "secret_token": mock_bot.secret_token,
            }
            result = MagicMock()
            result.inserted_id = bot_id
            return result

        mock_bot.insert = mock_insert
        return mock_bot

    async def mock_find_one(query):
        """Mock ChatBot.find_one method."""
        if (
            hasattr(query, "left")
            and hasattr(query.left, "key")
            and query.left.key == "id"
        ):
            search_id = str(query.right)
            if search_id in _mock_database["chatbots"]:
                data = _mock_database["chatbots"][search_id]
                mock_bot = MagicMock()
                mock_bot.id = ObjectId(data["_id"])
                mock_bot.name = data["name"]
                mock_bot.secret_token = data["secret_token"]

                mock_bot.name = data["name"]
                mock_bot.secret_token = data["secret_token"]

                return mock_bot
        return None

    mocker.patch(
        "app.routers.api.channel.ChatBot", side_effect=mock_chatbot_constructor
    )
    mocker.patch(
        "core.database.models.chat_bot.ChatBot", side_effect=mock_chatbot_constructor
    )
    mocker.patch(
        "core.database.models.chat_bot.ChatBot.find_one", side_effect=mock_find_one
    )

    yield


@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient]:
    """Get test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

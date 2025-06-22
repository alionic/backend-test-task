import pytest
from httpx import AsyncClient


def create_channel_data(**overrides):
    """Simple helper for creating test channel data."""
    data = {
        "name": "Test Channel",
        "channel_url": "https://example.com/webhook",
        "channel_token": "channel_token_123",
    }
    data.update(overrides)
    return data


@pytest.mark.asyncio
async def test_create_channel_success(client: AsyncClient):
    """Test creating a channel returns 201 with correct data."""
    channel_data = create_channel_data()

    response = await client.post("/api/channels", json=channel_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == channel_data["name"]
    assert "secret_token" in data
    assert "_id" in data
    assert len(data["secret_token"]) > 10


@pytest.mark.asyncio
async def test_create_channel_missing_name(client: AsyncClient):
    """Test creating channel without name returns 422."""
    channel_data = create_channel_data()
    del channel_data["name"]

    response = await client.post("/api/channels", json=channel_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_channel_missing_url(client: AsyncClient):
    """Test creating channel without URL returns 422."""
    channel_data = create_channel_data()
    del channel_data["channel_url"]

    response = await client.post("/api/channels", json=channel_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_channel_missing_token(client: AsyncClient):
    """Test creating channel without token returns 422."""
    channel_data = create_channel_data()
    del channel_data["channel_token"]

    response = await client.post("/api/channels", json=channel_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_multiple_channels_with_same_name(client: AsyncClient):
    """Test creating multiple channels with same name succeeds (they get different IDs)."""
    channel_data = create_channel_data(name="Duplicate Name Channel")

    response1 = await client.post("/api/channels", json=channel_data)
    response2 = await client.post("/api/channels", json=channel_data)

    assert response1.status_code == 201
    assert response2.status_code == 201

    data1 = response1.json()
    data2 = response2.json()

    assert data1["_id"] != data2["_id"]
    assert data1["secret_token"] != data2["secret_token"]
    assert data1["name"] == data2["name"] == channel_data["name"]


@pytest.mark.asyncio
async def test_channel_token_uniqueness(client: AsyncClient):
    """Test that multiple channels get unique secret tokens."""
    channel_data = create_channel_data()

    responses = []
    for i in range(3):
        response = await client.post("/api/channels", json=channel_data)
        assert response.status_code == 201
        responses.append(response.json())

    tokens = [resp["secret_token"] for resp in responses]

    assert len(set(tokens)) == len(tokens), f"Tokens not unique: {tokens}"


@pytest.mark.asyncio
async def test_get_channel_invalid_id_format(client: AsyncClient):
    """Test getting channel with invalid ID format returns 404."""
    invalid_id = "not_a_valid_object_id"

    response = await client.get(f"/api/channels/{invalid_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_channel_basic_lifecycle(client: AsyncClient):
    """Test creating a channel and verifying the response structure."""
    channel_data = create_channel_data(name="Lifecycle Test Channel")
    create_response = await client.post("/api/channels", json=channel_data)
    assert create_response.status_code == 201

    created_data = create_response.json()

    assert created_data["name"] == channel_data["name"]
    assert "secret_token" in created_data
    assert "_id" in created_data
    assert len(created_data["secret_token"]) > 10

    assert isinstance(created_data["name"], str)
    assert isinstance(created_data["secret_token"], str)
    assert isinstance(created_data["_id"], str)

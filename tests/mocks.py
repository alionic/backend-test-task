import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, patch


class DatabaseMockManager:
    """
    Comprehensive database mocking with stateful behavior simulation.

    Provides realistic database behavior for testing without requiring
    a real MongoDB instance.
    """

    def __init__(self):
        self.collections: Dict[str, Dict[str, Any]] = {
            "chatbots": {},
            "dialogues": {},
        }
        self._id_counter = 1000

    def _generate_object_id(self) -> str:
        """Generate a mock ObjectId for document insertion"""
        self._id_counter += 1
        return f"mock_id_{self._id_counter}"

    async def mock_chatbot_insert(self, document: Dict[str, Any]) -> AsyncMock:
        """Mock ChatBot.insert() with realistic behavior"""
        doc_id = self._generate_object_id()
        document["_id"] = doc_id
        self.collections["chatbots"][doc_id] = document.copy()

        result = AsyncMock()
        result.inserted_id = doc_id
        return result

    async def mock_chatbot_find_one(
        self, query: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Mock ChatBot.find_one()"""
        for doc_id, document in self.collections["chatbots"].items():
            if self._matches_query(document, query):
                return document
        return None

    async def mock_chatbot_find(
        self, query: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Mock ChatBot.find()"""
        if query is None:
            return list(self.collections["chatbots"].values())

        results = []
        for document in self.collections["chatbots"].values():
            if self._matches_query(document, query):
                results.append(document)
        return results

    async def mock_chatbot_replace(
        self, document: Dict[str, Any], query: Dict[str, Any]
    ) -> AsyncMock:
        """Mock ChatBot.replace()"""
        doc_id = query.get("_id") or document.get("_id")
        if doc_id and doc_id in self.collections["chatbots"]:
            document["_id"] = doc_id
            self.collections["chatbots"][doc_id] = document.copy()

        result = AsyncMock()
        result.modified_count = 1 if doc_id else 0
        return result

    async def mock_chatbot_delete(self, query: Dict[str, Any]) -> AsyncMock:
        """Mock ChatBot.delete()"""
        deleted_count = 0
        to_delete = []

        for doc_id, document in self.collections["chatbots"].items():
            if self._matches_query(document, query):
                to_delete.append(doc_id)

        for doc_id in to_delete:
            del self.collections["chatbots"][doc_id]
            deleted_count += 1

        result = AsyncMock()
        result.deleted_count = deleted_count
        return result

    async def mock_dialogue_insert(self, document: Dict[str, Any]) -> AsyncMock:
        """Mock Dialogue.insert()"""
        doc_id = self._generate_object_id()
        document["_id"] = doc_id
        self.collections["dialogues"][doc_id] = document.copy()

        result = AsyncMock()
        result.inserted_id = doc_id
        return result

    async def mock_dialogue_find(
        self, query: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Mock Dialogue.find()"""
        if query is None:
            return list(self.collections["dialogues"].values())

        results = []
        for document in self.collections["dialogues"].values():
            if self._matches_query(document, query):
                results.append(document)
        return results

    async def mock_dialogue_delete_many(self, query: Dict[str, Any]) -> AsyncMock:
        """Mock Dialogue.delete_many()"""
        deleted_count = 0
        to_delete = []

        for doc_id, document in self.collections["dialogues"].items():
            if self._matches_query(document, query):
                to_delete.append(doc_id)

        for doc_id in to_delete:
            del self.collections["dialogues"][doc_id]
            deleted_count += 1

        result = AsyncMock()
        result.deleted_count = deleted_count
        return result

    def _matches_query(self, document: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """Simple query matching"""
        if not query:
            return True

        for key, value in query.items():
            if key not in document:
                return False
            if document[key] != value:
                return False
        return True

    def clear_all_collections(self):
        """Clear all mock collections"""
        self.collections = {
            "chatbots": {},
            "dialogues": {},
        }


class SimpleMockManager:
    """
    Basic mocking utilities for unit tests.

    Provides simple patches for external dependencies following
    """

    def __init__(self):
        self.active_patches = []

    def mock_token_generation(self) -> Mock:
        """Mock token generation"""
        mock_patch = patch(
            "core.schemas.generate_token", return_value="test_token_123456"
        )
        mock = mock_patch.start()
        self.active_patches.append(mock_patch)
        return mock

    def mock_llm_call(self) -> AsyncMock:
        """Mock LLM service calls"""
        mock_patch = patch(
            "predict.mock_llm_call.process_message", new_callable=AsyncMock
        )
        mock = mock_patch.start()
        mock.return_value = "Mocked LLM response"
        self.active_patches.append(mock_patch)
        return mock

    def mock_http_client(self) -> AsyncMock:
        """Mock HTTP client"""
        mock_patch = patch("httpx.AsyncClient", new_callable=AsyncMock)
        mock = mock_patch.start()
        self.active_patches.append(mock_patch)
        return mock

    def cleanup(self):
        """Stop all active patches"""
        for patch_obj in self.active_patches:
            patch_obj.stop()
        self.active_patches.clear()


class MockHTTPServer:
    """
    Mock HTTP server for testing external API integrations.

    Simulates external service responses for integration testing
    """

    def __init__(self):
        self.responses = {}
        self.request_history = []

    def add_response(
        self,
        url: str,
        method: str,
        response_data: Dict[str, Any],
        status_code: int = 200,
    ):
        """Add a mock response for specific URL and method"""
        key = f"{method.upper()}:{url}"
        self.responses[key] = {"data": response_data, "status_code": status_code}

    async def mock_request(self, method: str, url: str, **kwargs) -> AsyncMock:
        """Mock HTTP request with configured responses"""
        self.request_history.append({"method": method, "url": url, "kwargs": kwargs})

        key = f"{method.upper()}:{url}"
        if key in self.responses:
            response = AsyncMock()
            response.json.return_value = self.responses[key]["data"]
            response.status_code = self.responses[key]["status_code"]
            return response

        response = AsyncMock()
        response.json.return_value = {"status": "success"}
        response.status_code = 200
        return response

    def get_request_history(self) -> List[Dict[str, Any]]:
        """Get history of all mocked requests"""
        return self.request_history.copy()

    def clear_history(self):
        """Clear request history"""
        self.request_history.clear()


class WebhookTestMocks:
    """
    Mocks for webhook testing.
    """

    def __init__(self):
        self.webhook_calls = []
        self.auth_tokens = {}

    def mock_webhook_authentication(self, token: str, is_valid: bool = True):
        """Mock webhook authentication with configurable validity"""
        self.auth_tokens[token] = is_valid

    async def mock_webhook_processing(
        self, payload: Dict[str, Any], token: str
    ) -> Dict[str, Any]:
        """Mock complete webhook processing workflow"""
        self.webhook_calls.append(
            {
                "payload": payload,
                "token": token,
                "timestamp": asyncio.get_event_loop().time(),
            }
        )

        if token not in self.auth_tokens or not self.auth_tokens[token]:
            return {"status": "error", "message": "Invalid authentication token"}

        return {
            "status": "success",
            "message": "Webhook processed successfully",
            "processed_count": 1,
        }

    def get_webhook_calls(self) -> List[Dict[str, Any]]:
        """Get history of all webhook calls"""
        return self.webhook_calls.copy()

    def clear_webhook_history(self):
        """Clear webhook call history"""
        self.webhook_calls.clear()
        self.auth_tokens.clear()


database_mock = DatabaseMockManager()
simple_mock = SimpleMockManager()
http_mock = MockHTTPServer()
webhook_mock = WebhookTestMocks()

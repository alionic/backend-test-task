from beanie import Document


class ChatBot(Document):
    name: str
    secret_token: str
    channel_url: str
    channel_token: str

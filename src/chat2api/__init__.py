from fastapi import Request

from chat2api.api import APIClient
from chat2api.chat import ChatServer


class Chat2API:
    def __init__(self, client: APIClient, server: ChatServer):
        self.client = client
        self.server = server

    async def response(self, request: Request):
        await self.client.parse_request(request)
        return self.client.response(self.server.answer_stream())

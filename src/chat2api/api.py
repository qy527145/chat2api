import json
from abc import abstractmethod
from typing import Iterable

from fastapi import Request
from starlette.responses import StreamingResponse

from chat2api.util import now, FIND_CHAT_BY_QUESTION


class APIClient:

    @abstractmethod
    async def parse_request(self, *args, **kwargs):
        pass

    @abstractmethod
    def response(self, *args, **kwargs):
        pass


class OpenaiAPI(APIClient):
    def __init__(self):
        self.context_id = None
        self.question = None
        self.model = None
        self.stream = None

    async def parse_request(self, request: Request, *args, **kwargs):
        request_json = await request.json()
        messages = request_json['messages']
        if len(messages) > 2:
            # 上下文
            for msg in messages:
                if msg['role'] == 'user':
                    self.context_id = FIND_CHAT_BY_QUESTION.get(msg['content'])
                    break
        self.question = request_json['messages'][-1]['content']
        self.model = request_json['model']
        self.stream = request_json.get('stream')

    def response(self, stream):
        if self.stream:
            return StreamingResponse(self.response_stream(stream), media_type="text/event-stream")
        else:
            return self.response_sync(''.join(stream))

    def response_stream(self, words: Iterable):
        for word in words:
            yield 'data: ' + json.dumps({
                'id': f'chatcmpl-{now()}',
                'object': "chat.completion.chunk",
                'created': now(),
                'model': self.model,
                'choices': [{
                    'index': 0,
                    'delta': {
                        "role": "assistant",
                        'content': word,
                    },
                    'finish_reason': None if word else 'stop'
                }]
            }, ensure_ascii=False) + '\n\n'
        yield 'data: [DONE]\n\n'

    def response_sync(self, words: str):
        return {
            'id': f'chatcmpl-{now()}',
            'object': "chat.completion",
            'created': now(),
            'model': self.model,
            'choices': [{
                'index': 0,
                'message': {
                    "role": "assistant",
                    'content': words,
                },
            }]
        }

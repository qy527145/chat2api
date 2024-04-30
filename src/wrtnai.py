import json
import os
import base64
import time

import requests
import uvicorn
from fastapi import Request, Response, FastAPI
from starlette.middleware.cors import CORSMiddleware

from chat2api import ChatServer, Chat2API
from chat2api.api import OpenaiAPI
from chat2api.util import now, LRUCache, is_summary


class WrtnAi(ChatServer):
    MODELS = ['gpt-4']

    def __init__(self, client: OpenaiAPI, refresh_token, proxies):
        self.client = client
        self.refresh_token = refresh_token
        self.access_token = None
        self.session_arg = None
        self.proxies = proxies

    def is_expired(self):
        if not self.access_token:
            return True
        message, signature = self.access_token.rsplit('.', 1)
        header, payload = message.split('.')
        payload = payload + '=' * - (len(payload) % - 4)
        # signature = signature + '=' * - (len(signature) % - 4)
        exp = json.loads(base64.b64decode(payload).decode()).get('exp')
        return exp - time.time() < 60

    def get_access_token(self):
        if not self.is_expired():
            return self.access_token
        url = 'https://api.wrtn.ai/be/auth/refresh'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'refresh': self.refresh_token,
        }
        resp = requests.post(url, headers=headers, proxies=self.proxies)
        resp.raise_for_status()
        self.access_token = resp.json()['data']['accessToken']
        return self.access_token

    def get_session_arg(self):
        if self.session_arg:
            return self.session_arg
        url = 'https://api.wrtn.ai/be/chat'
        headers = {
            'Authorization': 'Bearer {}'.format(self.get_access_token()),
        }
        resp = requests.post(url, headers=headers, proxies=self.proxies,
                             json={"unitId": "65d591e80c06023ae70af73a", "type": "model"})
        resp.raise_for_status()
        self.session_arg = resp.json()['data']['_id']
        return self.session_arg

    def get_message_arg(self, question):
        url = f'https://william.wow.wrtn.ai/chat/v3/{self.get_session_arg()}/start?platform=web&user=tmpkeesyh6cy8g@king361.cf&model=gpt4'
        headers = {
            'Authorization': 'Bearer {}'.format(self.get_access_token()),
        }
        resp = requests.post(url, headers=headers, proxies=self.proxies,
                             json={"message": f"{question}", "reroll": False, "images": []})
        resp.raise_for_status()
        return resp.json()['data']

    def answer_stream(self):
        question = self.client.question
        if is_summary(question):
            yield '闲聊'
        else:
            url = f'https://william.wow.wrtn.ai/chat/v3/{self.get_session_arg()}/{self.get_message_arg(question)}?model=gpt4&platform=web&user=tmpkeesyh6cy8g@king361.cf'
            headers = {
                'Authorization': 'Bearer {}'.format(self.get_access_token()),
            }
            resp = requests.get(url, headers=headers, proxies=self.proxies, stream=True)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            lines = resp.iter_lines(decode_unicode=True)
            for data in lines:
                if data.startswith('data:'):
                    info = json.loads(data[5:])
                    word = info.get('chunk')
                    if word:
                        print(word, end='')
                        yield word


app = FastAPI(title="PopAi Chat", description="PopAi Chat")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/v1/models')
def list_models():
    return {
        "object": "list",
        "data": [{
            "id": m,
            "object": "model",
            "created": now(),
            "owned_by": "popai"
        } for m in WrtnAi.MODELS]
    }


@app.options('/v1/chat/completions')
async def pre_chat():
    return Response()


@app.post('/v1/chat/completions')
async def chat(request: Request):
    return await chat2api_server.response(request)


if __name__ == '__main__':
    REFRESH_TOKEN = os.getenv('REFRESH_TOKEN')
    assert REFRESH_TOKEN, 'REFRESH_TOKEN must be set'
    FIND_CHAT_BY_QUESTION = LRUCache(1000)
    PROXY = os.environ.get("PROXY")
    if PROXY:
        PROXY = {'all': PROXY}
    else:
        PROXY = None

    cli = OpenaiAPI()
    chat2api_server = Chat2API(cli, WrtnAi(cli, REFRESH_TOKEN, PROXY))
    uvicorn.run(app, host='0.0.0.0', port=5000)

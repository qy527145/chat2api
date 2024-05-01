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
    MODELS = ['gpt4', 'gpt3.5', 'gpt3.5_16k', 'palm2', 'gpt4v', 'gpt4t', 'wrtn_search', 'claude_instant', 'claude2.1',
              'sdxl', 'sdxl_beta', 'sdxl_jp', 'dalle3', 'haiku', 'sonnet', 'GPT4', 'GPT3.5', 'GPT3.5_16K', 'PALM2',
              'fine-tune-blog', 'GPT4V', 'GPT4T', 'WRTN_SEARCH', 'CLAUDE_INSTANT', 'CLAUDE2.1', 'HAIKU', 'SONNET',
              'stable-diffusion-xl-beta-v2-2-2', 'SDXL', 'SDXL_JP', 'DALLE3']

    def __init__(self, client: OpenaiAPI, refresh_token, proxies):
        self.client = client
        self.refresh_token = refresh_token
        self.access_token = None
        self.user_id = None
        self.unit_id = None
        self.user_email = None
        self.session_arg = None
        self.proxies = proxies
        self.get_access_token()

    def get_unit_id(self):
        if self.unit_id:
            return self.unit_id
        url = 'https://api.wrtn.ai/be/chat'
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.get_access_token()),
            'Origin': 'https://wrtn.ai',
            'Platform': 'web',
            'Priority': 'u=1, i',
            'Referer': 'https://wrtn.ai/',
            'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Wrtn-Locale': 'ko-KR'
        }
        resp = requests.get(url, headers=headers, proxies=self.proxies)
        resp.raise_for_status()
        chats = resp.json()['data']
        if len(chats) == 0:
            raise Exception('首次需要在官网创建一个对话')
        self.unit_id = chats[0]['tempUnit']['_id']
        return self.unit_id

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
            'Origin': 'https://wrtn.ai',
            'Referer': 'https://wrtn.ai/',
            'Refresh': self.refresh_token,
            'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        }
        resp = requests.post(url, headers=headers, proxies=self.proxies)
        resp.raise_for_status()
        self.access_token = resp.json()['data']['accessToken']
        message, signature = self.access_token.rsplit('.', 1)
        header, payload = message.split('.')
        payload = payload + '=' * - (len(payload) % - 4)
        payload_json = json.loads(base64.b64decode(payload).decode())
        self.user_id = payload_json.get('id')
        self.user_email = payload_json.get('email')
        return self.access_token

    def get_session_arg(self):
        if self.session_arg:
            return self.session_arg
        url = 'https://api.wrtn.ai/be/chat'
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.get_access_token()),
            'Origin': 'https://wrtn.ai',
            'Platform': 'web',
            'Priority': 'u=1, i',
            'Referer': 'https://wrtn.ai/',
            'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Wrtn-Locale': 'ko-KR'
        }
        resp = requests.post(url, headers=headers, proxies=self.proxies,
                             json={"unitId": f"{self.get_unit_id()}", "type": "model"})
        resp.raise_for_status()
        self.session_arg = resp.json()['data']['_id']
        return self.session_arg

    def get_message_arg(self, question, model):
        url = f'https://william.wow.wrtn.ai/chat/v3/{self.get_session_arg()}/start?platform=web&user={self.user_email}&model={model}'
        headers = {
            'Authorization': 'Bearer {}'.format(self.get_access_token()),
            'Accept': 'application/json',
            'Origin': 'https://wrtn.ai',
            'Platform': 'web',
            'Priority': 'u=1, i',
            'Referer': 'https://wrtn.ai/',
            'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Wrtn-Locale': 'ko-KR',
        }
        resp = requests.post(url, headers=headers, proxies=self.proxies,
                             json={"message": f"{question}", "reroll": False, "images": []})
        resp.raise_for_status()
        return resp.json()['data']

    def answer_stream(self):
        question = self.client.question
        model = self.client.model
        if model not in self.MODELS:
            model = 'gpt4'
        if is_summary(question):
            yield '闲聊'
        else:
            url = f'https://william.wow.wrtn.ai/chat/v3/{self.get_session_arg()}/{self.get_message_arg(question, model)}?model={model}&platform=web&user={self.user_email}&isChocoChip=false'
            headers = {
                'Authorization': 'Bearer {}'.format(self.get_access_token()),
                'Accept': 'text/event-stream',
                'Origin': 'https://wrtn.ai',
                'Priority': 'u=1, i',
                'Referer': 'https://wrtn.ai/',
                'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Wrtn-Locale': 'ko-KR',
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

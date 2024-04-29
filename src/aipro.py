import json
import os

import requests
import uvicorn
from fastapi import FastAPI, Request, Response
from starlette.middleware.cors import CORSMiddleware

from chat2api import Chat2API
from chat2api.api import OpenaiAPI
from chat2api.chat import ChatServer
from chat2api.util import LRUCache
from chat2api.util import now


class AiProChat(ChatServer):
    MODELS = {
        'gpt-3.5-turbo': 'https://chatpro.ai-pro.org/api/ask/openAI',
        'gpt-4-1106-preview': 'https://chatpro.ai-pro.org/api/ask/openAI',
        'gpt-4-pro-max': 'https://chatpro.ai-pro.org/api/ask/openAI',

        'chat-bison': 'https://chatpro.ai-pro.org/api/ask/google',
        'text-bison': 'https://chatpro.ai-pro.org/api/ask/google',
        'codechat-bison': 'https://chatpro.ai-pro.org/api/ask/google',

        'openchat_3.5': 'https://chatpro.ai-pro.org/api/ask/Opensource',
        'zephyr-7B-beta': 'https://chatpro.ai-pro.org/api/ask/Opensource',
    }

    def __init__(self, client: OpenaiAPI):
        self.client = client

    @staticmethod
    def get_url(model):
        if model in AiProChat.MODELS:
            return AiProChat.MODELS[model]
        return AiProChat.MODELS['gpt-4-pro-max']

    def answer_stream(self):
        question = self.client.question
        model = self.client.model
        context_id = None
        if len(self.client.messages) > 2:
            # 上下文
            for msg in self.client.messages:
                if msg['role'] == 'user':
                    context_id = FIND_CHAT_BY_QUESTION.get(msg['content'])
                    break
        stream = self.client.stream

        print('-' * 30, '\n')
        print('question: \n', question)
        print('-' * 30, '\n')
        print('answer: ')

        url = AiProChat.get_url(model)
        endpoint = url[url.rfind('/') + 1:]
        req_json = {
            "conversationId": context_id,
            'parentMessageId': FIND_LAST_MSG_IN_CHAT.get(context_id, '00000000-0000-0000-0000-000000000000'),
            "text": question,
            "endpoint": endpoint,
            "model": model
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
            'Origin': 'https://chatpro.ai-pro.org',
            'Referer': 'https://chatpro.ai-pro.org/chat/new',
        }
        proxy = os.environ.get('PROXY')
        if proxy:
            proxies = {'all': proxy}
        else:
            proxies = None
        resp = requests.post(url, json=req_json, headers=headers, proxies=proxies, stream=True)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
        last_text = ''
        lines = resp.iter_lines(decode_unicode=True)
        for data in lines:
            # 首条消息包含对话信息
            if data.startswith('data'):
                infos = json.loads(data[6:])
                context_id = infos['message']['conversationId']
                FIND_CHAT_BY_QUESTION[question] = context_id
                if stream:
                    msg_id = infos['message']['messageId']
                    FIND_LAST_MSG_IN_CHAT[context_id] = msg_id
                break
        for data in lines:
            if data.startswith('data'):
                infos = json.loads(data[6:])
                if 'text' in infos:
                    text = infos['text']
                    word = text[len(last_text):]
                    print(word, end='')
                    yield word
                    last_text = text
        print()


class AiProDraw(ChatServer):
    def __init__(self, client: OpenaiAPI):
        self.client = client

    def answer_stream(self):
        yield "这是图片：\n"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
            'Origin': 'https://chatpro.ai-pro.org',
            'Referer': 'https://chatpro.ai-pro.org/chat/new',
        }
        resp = requests.post(
            'https://app.ai-pro.org/api/aipsd/v2/dream-photo-create',
            headers=headers,
            data={
                'payload': json.dumps(
                    {
                        "positive": f"{self.client.question}",
                        "negative": "",
                        "height": "512",
                        "width": "512",
                        "model": "RealitiesEdgeXL_4"
                    }
                ),
                'slug': 'dream-photo',
                'surfToken': '51dc3d9891224881'
            }
        )
        for base_img in resp.json()['data']['images']:
            # todo 图床
            yield f"![asd](data:img/png;base64,{base_img})"


class AiPro(ChatServer):
    def __init__(self, client: OpenaiAPI):
        self.client = client
        self.chat = AiProChat(client)
        self.draw = AiProDraw(client)

    def answer_stream(self):
        if self.client.question.startswith('画图：'):
            return self.draw.answer_stream()
        else:
            return self.chat.answer_stream()


app = FastAPI()

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
            "owned_by": AiProChat.MODELS[m].rsplit('/', 1)
        } for m in AiProChat.MODELS]
    }


@app.options('/v1/chat/completions')
async def pre_chat():
    return Response()


@app.post('/v1/chat/completions')
async def chat(request: Request):
    cli = OpenaiAPI()
    ser = AiPro(cli)
    return await Chat2API(cli, ser).response(request)


if __name__ == '__main__':
    FIND_CHAT_BY_QUESTION = LRUCache(1000)
    FIND_LAST_MSG_IN_CHAT = LRUCache(1000)
    uvicorn.run(app, host='0.0.0.0', port=5000)

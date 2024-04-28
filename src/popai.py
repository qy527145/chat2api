import json
import os

import requests
import uvicorn
from fastapi import Request, Response, FastAPI
from starlette.middleware.cors import CORSMiddleware

from chat2api import ChatServer, Chat2API
from chat2api.api import OpenaiAPI
from chat2api.util import now, LRUCache


class PopAi(ChatServer):
    MODELS = {
        'gpt-3.5': 'Standard',
        'gpt-4': 'GPT-4',
        'internet': 'Web Search',
        'draw': 'Image generation',
    }

    def __init__(self, client: OpenaiAPI, authorization, gtoken):
        self.client = client
        self.authorization = authorization
        self.gtoken = gtoken

    def answer_stream(self):
        question = self.client.question
        model = PopAi.MODELS.get(self.client.model, 'GPT-4')

        proxy = os.environ.get("PROXY")
        if proxy:
            proxies = {'all': proxy}
        else:
            proxies = None
        context_id = None
        if len(self.client.messages) > 2:
            # 上下文
            for msg in self.client.messages:
                if msg['role'] == 'user':
                    context_id = FIND_CHAT_BY_QUESTION.get(msg['content'])
                    if context_id:
                        break

        if context_id is None:
            channel_resp = requests.post(
                'https://api.popai.pro/api/v1/chat/getChannel',
                headers={'Authorization': self.authorization},
                json={
                    "model": model,
                    "templateId": "",
                    "message": question,
                    "language": "English",
                    "fileType": None
                },
                proxies=proxies,
            )
            channel_resp.raise_for_status()
            context_id = channel_resp.json()['data']['channelId']

        print('-' * 30, '\n')
        print('question: \n', question)
        print('-' * 30, '\n')
        print('answer: ')

        url = 'https://api.popai.pro/api/v1/chat/send'
        headers = {
            "accept": "text/event-stream",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,zh-HK;q=0.6",
            "app-name": "popai-web",
            "authorization": self.authorization,
            "content-type": "application/json",
            "device-info": "{web_id:k-s8Xp4S9LEmrHghBhT2m,baidu_id:18f1ff567e243687188711}",
            "gtoken": self.gtoken,
            "language": "en",
            "origin": "https://www.popai.pro",
            "priority": "u=1, i",
            "referer": "https://www.popai.pro/",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
        }

        req_json = {
            "isGetJson": True,
            "version": "1.3.6",
            "language": "zh-CN",
            "channelId": context_id,
            "message": question,
            "model": PopAi.MODELS.get(model, 'GPT-4'),
            "messageIds": [],
            "improveId": None,
            "richMessageId": None,
            "isNewChat": False,
            "action": None,
            "isGeneratePpt": False,
            "isSlidesChat": False,
            "imageUrls": [],
            "roleEnum": None,
            "pptCoordinates": "",
            "translateLanguage": None,
            "docPromptTemplateId": None
        }
        resp = requests.post(url, json=req_json, headers=headers, proxies=proxies, stream=True)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
        lines = resp.iter_lines(decode_unicode=True)
        for data in lines:
            # 首条消息是用户提问，舍掉
            if data.startswith('data:'):
                infos = json.loads(data[5:])
                context_id = infos[0].get('channelId')
                FIND_CHAT_BY_QUESTION[question] = context_id
                break
        for data in lines:
            if data.startswith('data:'):
                infos = json.loads(data[5:])
                for info in infos:
                    # msg_id = info.get('messageId')
                    word = info.get('content')
                    if word:
                        print(word, end='')
                        yield word
        print()


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
            "owned_by": "popai"
        } for m in PopAi.MODELS]
    }


@app.options('/v1/chat/completions')
async def pre_chat():
    return Response()


@app.post('/v1/chat/completions')
async def chat(request: Request):
    cli = OpenaiAPI()
    ser = PopAi(cli, AUTHORIZATION, GTOKEN)
    return await Chat2API(cli, ser).response(request)


if __name__ == '__main__':
    AUTHORIZATION = os.environ.get('AUTHORIZATION')
    GTOKEN = os.environ.get('GTOKEN')
    assert not AUTHORIZATION or GTOKEN, 'AUTHORIZATION and GTOKEN must be set'
    FIND_CHAT_BY_QUESTION = LRUCache(1000)

    uvicorn.run(app, host='0.0.0.0', port=5000)

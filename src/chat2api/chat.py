import json
import os
from abc import abstractmethod

import requests

from chat2api.api import OpenaiAPI
from chat2api.util import FIND_LAST_MSG_IN_CHAT, FIND_CHAT_BY_QUESTION


class ChatServer:

    @abstractmethod
    def answer_stream(self, *args, **kwargs):
        pass


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
        context_id = self.client.context_id
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
                chat_id = infos['message']['conversationId']
                FIND_CHAT_BY_QUESTION[question] = chat_id
                if stream:
                    msg_id = infos['message']['messageId']
                    FIND_LAST_MSG_IN_CHAT[chat_id] = msg_id
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
        resp = requests.post(
            'https://app.ai-pro.org/api/aipsd/v2/dream-photo-create',
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

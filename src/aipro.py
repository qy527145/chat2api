import uvicorn
from fastapi import FastAPI, Request, Response
from starlette.middleware.cors import CORSMiddleware

from chat2api import Chat2API
from chat2api.api import OpenaiAPI
from chat2api.chat import AiProChat, AiPro
from chat2api.util import LRUCache

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('v1/models')
def list_models():
    return list(AiProChat.MODELS.keys())


@app.options('/v1/chat/completions')
async def pre_chat():
    return Response()


@app.post('/v1/chat/completions')
async def chat(request: Request):
    # 解析接收到的请求体为POST请求
    cli = OpenaiAPI()
    ser = AiPro(cli)
    return await Chat2API(cli, ser).response(request)


if __name__ == '__main__':
    find_chat_by_question = LRUCache(1000)
    find_last_msg_in_chat = LRUCache(1000)
    uvicorn.run(app, host='0.0.0.0', port=5000)

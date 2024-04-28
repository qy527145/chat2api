import uvicorn
from fastapi import FastAPI, Request, Response
from starlette.middleware.cors import CORSMiddleware

from chat2api import Chat2API
from chat2api.api import OpenaiAPI
from chat2api.chat import AiProChat, AiPro

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
    cli = OpenaiAPI()
    ser = AiPro(cli)
    return await Chat2API(cli, ser).response(request)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000)

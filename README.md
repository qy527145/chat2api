# 用户手册

## docker 启动

```bash

docker run --name popai --restart=always -d -p 8888:5000 -e AUTHORIZATION=<AUTHORIZATION> -e GTOKEN=<GTOKEN> wmymz/chat2api popai.py

#aipro
docker run --name aipro --restart=always -d -p 8881:5000 -e PYTHONUNBUFFERED=1 -e PROXY=http://proxyip:port wmymz/aipro
# popai
docker run --name popai --restart=always -d -p 8882:5000 -e PYTHONUNBUFFERED=1 -e PROXY=http://proxyip:port -e AUTHORIZATION=<AUTHORIZATION> -e GTOKEN=<GTOKEN> wmymz/popai
# wrtnai
docker run --name wrtnai --restart=always -d -p 8883:5000 -e PYTHONUNBUFFERED=1 -e PROXY=http://proxyip:port -e REFRESH_TOKEN=<REFRESH_TOKEN> wmymz/wrtnai

```

## docker compose

```yaml
services:
  aipro:
    image: wmymz/chat2api:latest
    command: popai.py
    restart: always
    ports:
      - "8881:5000"
    environment:
      PYTHONUNBUFFERED: 1
      PROXY: "http://proxyip:port"
  popai:
    image: wmymz/chat2api:latest
    command: popai.py
    restart: always
    ports:
      - "8882:5000"
    environment:
      PYTHONUNBUFFERED: 1
      PROXY: "http://proxyip:port"
      AUTHORIZATION: "<AUTHORIZATION>"
      GTOKEN: "<GTOKEN>"
  wrtnai:
    image: wmymz/chat2api:latest
    command: wrtnai.py
    restart: always
    ports:
      - "8883:5000"
    environment:
      PYTHONUNBUFFERED: 1
      PROXY: "http://proxyip:port"
      REFRESH_TOKEN: "<REFRESH_TOKEN>"
```

# 开发手册

## 开发步骤

> 具体请参考aipro的demo

* 实现APIClient
* 实现ChatServer
* 使用Chat2API糊一个接口

## 打包docker镜像

```bash
# 构建镜像，上传Docker hub
docker compose build --no-cache
docker compose push 
```
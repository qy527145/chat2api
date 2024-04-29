# 用户手册

## docker 启动

```bash
docker run --name popai --restart=always -d -p 8888:5000 -e AUTHORIZATION=<AUTHORIZATION> -e GTOKEN=<GTOKEN> wmymz/chat2api popai.py
# ip被ban后需要配合http代理
docker run --name popai --restart=always -d -p 8888:5000 -e PYTHONUNBUFFERED=1 -e AUTHORIZATION=<AUTHORIZATION> -e GTOKEN=<GTOKEN> -e PROXY=http://proxyip:port wmymz/chat2api popai.py

```

## docker compose

```yaml
services:
  aipro:
    image: wmymz/chat2api:latest
    # command: aipro.py
    command: popai.py
    restart: always
    ports:
      - "8888:5000"
    environment:
      PYTHONUNBUFFERED: 1
      PROXY: "http://proxyip:port"
      AUTHORIZATION: "<AUTHORIZATION>"
      GTOKEN: "<GTOKEN>"
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
docker build --no-cache -t wmymz/chat2api .
docker push wmymz/chat2api
```
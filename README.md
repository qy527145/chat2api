# 用户手册

## docker 启动

```bash
docker run --name popai --restart=always -d -p 8888:5000 -e AUTHORIZATION=<AUTHORIZATION> -e GTOKEN=<GTOKEN> wmymz/popai
# ip被ban后需要配合http代理
docker run --name popai --restart=always -d -p 8888:5000 -e AUTHORIZATION=<AUTHORIZATION> -e GTOKEN=<GTOKEN> -e PROXY=http://proxyip:port wmymz/popai

```

## docker compose

```yaml
services:
  aipro:
    image: wmymz/popai:latest
    restart: always
    ports:
      - "8888:5000"
    environment:
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
# 虚拟环境
python3 -m venv venv
source venv/bin/activate
python install -r requirements.txt

# 打包单文件可执行程序（以popai为例）
cd src
pyinstaller -F popai.py -n popai

# 构建镜像，上传Docker hub
docker build -t wmymz/popai .
docker push wmymz/popai
```
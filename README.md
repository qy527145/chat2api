# 用户手册

## docker 启动

```bash
docker run --name aipro --restart=always -d -p 8888:5000 wmymz/aipro`
# ip被ban后需要配合http代理
docker run --name aipro --restart=always -d -e PROXY=http://proxyip:port -p 8888:5000 wmymz/aipro`
```

## docker compose

```yaml
services:
  aipro:
    image: wmymz/aipro:latest
    restart: always
    ports:
      - "8888:5000"
    environment:
      PROXY: "http://proxyip:port"
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

# 打包单文件可执行程序（以aipro为例）
cd src
pyinstaller -F aipro.py -n aipro

# 构建镜像，上传Docker hub
docker build -t wmymz/aipro .
docker push wmymz/aipro
```
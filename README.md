## 打包：

`pyinstaller -F aipro.py -n aipro`

## 构建镜像：

`docker build -t wmymz/aipro .`

## 上传镜像：

`docker push wmymz/aipro`

## 启动docker：

`docker run -d -p 6666:5000 wmymz/aipro`
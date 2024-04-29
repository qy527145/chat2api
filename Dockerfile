FROM python:alpine

COPY ./requirements.txt /app

WORKDIR /app

RUN pip install --no-cache-dir -U -r requirements.txt

COPY ./src /app

EXPOSE 5000

ENTRYPOINT ["python"]

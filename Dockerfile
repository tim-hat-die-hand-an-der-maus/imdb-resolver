FROM python:3.11-slim

WORKDIR /usr/src/app

ENV TZ=Europe/Berlin

ADD main.py .
ADD requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD uvicorn main:app --host 0.0.0.0

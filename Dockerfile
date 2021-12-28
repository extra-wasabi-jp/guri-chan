FROM python:3.8.11-slim-buster

WORKDIR /app
COPY ./app/ /app

RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

ENV API_PORT ${API_PORT}
ENV CHANNEL_ACCESS_TOKEN ${CHANNEL_ACCESS_TOKEN}
ENV CHANNEL_SECRET ${CHANNEL_SECRET}

CMD ["python", "manager.py"]

FROM python:3.8.11-slim-buster

WORKDIR /app
COPY ./app/ /app

RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

ENV API_PORT ${API_PORT}

ENV AWS_REGION ${AWS_REGION}
ENV AWS_ACCESS_KEY_ID ${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY ${AWS_SECRET_ACCESS_KEY}

ENV CHANNEL_ACCESS_TOKEN ${CHANNEL_ACCESS_TOKEN}
ENV CHANNEL_SECRET ${CHANNEL_SECRET}

CMD ["python", "manager.py"]

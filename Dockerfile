# build container in python base image

FROM python:3.11.8-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=docker:dind /usr/local/bin/docker /usr/local/bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

RUN \
    DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker} && \
    mkdir -p $DOCKER_CONFIG/cli-plugins && \
    curl -SL https://github.com/docker/compose/releases/download/v2.29.1/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose && \
    chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

COPY requirements.txt /
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app /app
RUN mkdir /compose
WORKDIR /app

CMD ["python", "main.py"]

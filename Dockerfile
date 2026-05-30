# build container in python base image

FROM python:3.13.11-slim-trixie

ARG HOOK_VERSION
ENV HOOK_VERSION=$HOOK_VERSION
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=docker:dind /usr/local/bin/docker /usr/local/bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl tini && \
    rm -rf /var/lib/apt/lists/*

RUN \
    DOCKER_CONFIG=/usr/lib/docker/cli-plugins && \
    mkdir -p $DOCKER_CONFIG && \
    curl -SL https://github.com/docker/compose/releases/download/v5.1.4/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/docker-compose && \
    chmod +x $DOCKER_CONFIG/docker-compose

COPY requirements.txt /
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app /app
RUN mkdir /compose
WORKDIR /app

ENTRYPOINT ["/bin/tini", "--"]
CMD ["python", "main.py"]

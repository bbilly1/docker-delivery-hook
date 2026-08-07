# build container in python base image

FROM python:3.13.11-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=docker:29-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker:29-cli /usr/local/libexec/docker/cli-plugins/ \
    /usr/local/lib/docker/cli-plugins/

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl tini && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app /app
RUN mkdir /compose
WORKDIR /app

ARG HOOK_VERSION
ENV HOOK_VERSION=$HOOK_VERSION

ENTRYPOINT ["/bin/tini", "--"]
CMD ["python", "main.py"]

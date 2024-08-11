# Docker Delivery Hook
Webhook endpoint to trigger docker container rebuild

## Usecase
- You build and push your container images from a CI/CD pipeline to a container registry
- You run your own container from a VM created from a docker compose file
- You are looking for a way to pull and recreate your docker image after CI/CD completes
- You want to avoid polling the container registry on an interval
- You want to avoid setting up SSH from the pipeline into your server

## Install

Docker Compose example:

```yml
services:
  docker-delivery-hook:
    image: ghcr.io/bbilly1/docker-delivery-hook
    container_name: docker-delivery-hook
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /path/to/docker-compose.yml:/path/to/docker-compose.yml
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      SECRET_KEY: "your-very-secret-key"
```

Make sure you specify the `container_name` key for all services on your host system, as that is used for identification.

### Volumes

- Docker Socket: Mount host docker socket into the container to allow the container to execute docker commands as the host user. See security considerations below.
- Compose File: Crucially mount the docker-compose.yml file exactly at the same absolute path inside the container as outside on the host machine. Docker tracks the compose environment with the labels `com.docker.compose.project.config_files` and `com.docker.compose.project.working_dir`. Interacting with existing containers requires the same compose location otherwise docker will treat this as a separate compose file.

### Environment Variables

Configure the API with these environment variables:

- `SECRET_KEY`: Required, shared secret key for signature validation.
- `UVICORN_PORT`: Optional, overwrite internal web server port from default 8000.
- `SHOW_DOCS`: Optional, set to anything except an empty string to show default FastAPI docs. Only for your local dev environment.

## Endpoints

This API implements these endpoints:

- `/pull`: Rebuilding the container by pulling the new image. Only applicable if your compose file defines an `image` key. That is equivalent to:
```bash
docker compose pull container_name && docker compose up -d container_name
```
- `/build`: Rebuild the container by building locally. Only applicable if your compose file defines a `build` key. Be aware that you either need to pull the context from a remote like git or mount the correct build context into the container and not just the compose file. That is equivalent to:
```bash
docker compose up -d --build container_name
```

These endpoints are async. Meaning after request validation will return while the docker commands will process in the background.

## Pipeline Example

```bash
PAYLOAD='{"container_name": "my-container-name"}'
SECRET_KEY="your-very-secret-key"
TIMESTAMP=$(date +%s)
MESSAGE="${PAYLOAD}${TIMESTAMP}"
SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$SECRET_KEY" | cut -d " " -f 2)

curl -X POST -H "Content-Type: application/json" \
 	-H "X-Timestamp: $TIMESTAMP" \
 	-H "X-Signature: $SIGNATURE" \
 	-d "$PAYLOAD" \
 	$API_ENDPOINT
```

Explanation:
- `SECRET_KEY`: That's the shared secret between your pipeline and the API container. That is usually stored as a secret variable in your pipeline.
- `TIMESTAMP`: UTC epoch timestamp.
- `MESSAGE`: String concatenated from Payload and Timestamp.
- `SIGNATURE`: SHA256 HMAC signature from the message. See below for additional examples.
- `PAYLOAD`: JSON body with key `"container_name"` and value the container name as defined in your compose file.

## Signature building

Depending what you have available in your pipeline environment, you might want to choose one over the other. Here are some examples:

Using OpenSSL:
```bash
SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$SECRET_KEY" | cut -d " " -f 2)
```

Using Python standard library:
```bash
SIGNATURE=$(python -c "import hmac, hashlib; print(hmac.new(b'$SECRET_KEY', b'$MESSAGE', hashlib.sha256).hexdigest())")
```

Using NodeJS:
```bash
SIGNATURE=$(node -e "
  const crypto = require('crypto');
  const signature = crypto.createHmac('sha256', '$SECRET_KEY').update('$MESSAGE').digest('hex');
  console.log(signature);
")
```

## Security Consideration

If you see any flaws here, reach out.

### Verifications

- Signature Verification: By passing the `X-Signature` header with your request, the API will be able to verify that the origin has the same `SECRET_KEY` as the API and the origin receives the same data as expected.
- Timestamp: By passing the `X-Timestamp` header plus by using the timestamp in the message to verify the signature, you are able to guarantee that even an intercepted message wouldn't be able to be reused in a future time.
- Container Name: The container name you send with the payload is verified by docker directly first by checking all existing containers and searching for a match.
- Compose Validation: The compose file location is validated by inspecting the container name
- Predefined commands: The commands executed are predefined. The variables going into the commands are validated as described above.

### SSH in your pipeline

Alternate approach to solve this problem is to setup SSH in your pipeline. That usually means to create a least privileged user on your VM, lock down SSH for that user to limit what that user is allowed to do, then add the private SSH key in your pipeline. Then as part of your pipeline, you'll register the key, login to your VM, and run the needed commands.

That has a few downsides:
- Requires configurations on the VM. That can be automated with scripting or tools like Ansible, but that's something that needs to be maintained additionally to your application code base.
- Another SSH key on the VM is required to basically just execute a single command. That is an additional exposure that you might want to avoid.
- The private key needs to be in the CI/CD pipeline and will be accessible by everyone with access to the pipeline.
- That is difficult to manage with infrastructure as code. Having a CI/CD listener on your VM that can react to webhooks can be managed in your regular docker compose file. All can be committed to version control as part of your application, obviously except the `SECRET_KEY`.
- Needing SSH from your pipeline makes hardening your SSH exposure much more difficult. Depending on your environment you might not know all possible IPs from your runners and you might not allow SSH to be available to the internet unrestricted.

### Mounting docker socket
You might also want to read up on the implication for mounting `docker.sock` into the container. Verify the code first, use at your own risk before publishing that to the internet.

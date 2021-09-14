FROM python:3.8-alpine

# Ensures written logs are made available directly
ENV PYTHONUNBUFFERED=1

# Using tini to wrap our process, we react to SIGTERM quickly among other
# things. We use tini-static instead of tini as it embeds dependencies missing
# in alpine.
RUN ARCH=$(uname -m); \
    if [ "$ARCH" = x86_64 ]; then ARCH=amd64; fi; \
    if [ "$ARCH" = aarch64 ]; then ARCH=arm64; fi; \
    wget -qO /tini "https://github.com/krallin/tini/releases/download/v0.19.0/tini-static-$ARCH" \
 && chmod +x /tini

# Install docker-image-cleaner
COPY . /tmp/cleaner
RUN pip install --no-cache /tmp/cleaner

ENTRYPOINT [ "/tini", "--", "/usr/local/bin/acme-secret-sync.py" ]

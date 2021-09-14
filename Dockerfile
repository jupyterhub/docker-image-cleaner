FROM python:3.8-slim-buster

COPY . /tmp/cleaner
RUN pip install --no-cache /tmp/cleaner

# set PYTHONUNBUFFERED to ensure output is produced
ENV PYTHONUNBUFFERED=1
CMD ["docker-image-cleaner"]

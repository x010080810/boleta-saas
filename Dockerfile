FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
  libpango-1.0-0 libpangocairo-1.0-0 \
  libgdk-pixbuf-2.0-0 libffi-dev \
  shared-mime-info && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN mkdir -p /tmp/uploads /tmp/output /tmp/backups

EXPOSE 8000

RUN chmod +x entrypoint.sh

CMD ./entrypoint.sh

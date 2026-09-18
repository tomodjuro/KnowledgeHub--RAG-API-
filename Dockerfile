FROM python:3.10-slim

# Sprečava pisanje .pyc datoteka i osigurava direktan ispis u logove
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalacija sistemskih zavisnosti
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Kopiranje i instalacija Python biblioteka
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiranje cijelog koda projekta
COPY . .

# Stvaranje potrebnih mapa
RUN mkdir -p docs chroma_db
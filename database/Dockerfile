FROM python:3.10-slim

# Wir nennen das Arbeitsverzeichnis '/code' (oder '/src'), um Verwirrung zu vermeiden
WORKDIR /code

# 1. Requirements kopieren und installieren (für Docker-Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Den Rest kopieren
# Damit landet dein Ordner "app" in "/code/app"
COPY . .

# 3. Der wichtige Teil: Der Pfad zum Starten
# Statt "main:app" heißt es jetzt "app.main:app"
# Python sucht im Ordner "app" nach der Datei "main"
# Verwende sh -c, um Umgebungsvariablen korrekt aufzulösen und einen Default-Port zu setzen
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
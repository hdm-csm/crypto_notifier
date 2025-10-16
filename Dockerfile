# Basis-Image: offizielle Python 3.12 Version
# Slim: kleineres Image ohne zusätzliche Tools (python binaries + pips sind installiert)
FROM python:3.12-slim

# Arbeitsverzeichnis im Container setzen
# Alle nachfolgenden Befehle laufen relativ zu /app
# Bei Container Start ist /app das Anfangsverzeichnis
WORKDIR /app

# Kopiert requirements.txt in den container nach /app/requirements.txt
COPY requirements.txt .

#  installieren alle Pakete aus requirements.txt innerhalb des Containers
RUN pip install -r requirements.txt

# Copiert gestamten Projektinhalt ./test-ci-cd/ in den Container nach /app/
# Das schließt app/, tests/, Dockerfile usw. ein
COPY . .

# Standardbefehl, der ausgeführt wird, wenn der Container startet
# Führt das Python-Skript app/hello.py aus
CMD ["python", "app/hello.py"]

## docker build → Tells Docker to build an image from a Dockerfile.
## -t test-ci-cd → Tags the image with the name test-ci-cd. You can later reference it by this name.
## . → The build context, Docker will look for a Dockerfile in the current directory and include all files in the current folder for the build.
# docker build -t test-ci-cd .

## docker run → Creates a new container from an image and executes it.
## test-ci-cd → The image to use (built in the previous step).
# docker run test-ci-cd

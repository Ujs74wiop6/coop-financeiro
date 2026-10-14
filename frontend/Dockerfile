FROM python:3.12-slim

WORKDIR /app
COPY . .

EXPOSE 8080
# Servidor estático embutido no Python: só entrega os arquivos HTML/CSS/JS.
CMD ["python", "-m", "http.server", "8080", "--directory", "/app"]

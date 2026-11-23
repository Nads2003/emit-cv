FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Embeddings transformers (optionnel, lourd) : remplacer par `pip install -r requirements-ml.txt`
COPY . .
RUN useradd -m appuser && mkdir -p /app/uploads && chown -R appuser /app && chmod +x entrypoint.sh
USER appuser
EXPOSE 8000
# Santé : /ready vérifie que la base répond (Docker redémarre/exclut le conteneur sinon)
HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=4).status == 200 else 1)"
CMD ["./entrypoint.sh"]

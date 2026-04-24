FROM python:3.12-slim
WORKDIR /app
COPY services /app/services
RUN pip install --no-cache-dir -r /app/services/content/requirements.txt
ENV PYTHONPATH=/app
CMD ["sh", "-c", "uvicorn services.content.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

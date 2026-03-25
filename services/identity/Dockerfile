FROM python:3.12-slim
WORKDIR /app
COPY services /app/services
RUN pip install --no-cache-dir -r /app/services/identity/requirements.txt
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.identity.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

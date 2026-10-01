FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ app/

# The SQLite database lives in a volume mounted at /data.
ENV DATABASE_URL=sqlite:////data/notify_router.db
VOLUME /data
EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]

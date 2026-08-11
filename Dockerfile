FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY app ./app
COPY scripts ./scripts
COPY data/sample_docs ./data/sample_docs
COPY data/eval_questions.json ./data/eval_questions.json

RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/app/data/insight.db
ENV BM25_INDEX_PATH=/app/data/bm25.json
ENV UPLOAD_DIR=/app/data/uploads
ENV MILVUS_URI=http://milvus:19530

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

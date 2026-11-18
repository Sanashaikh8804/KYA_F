FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY kya kya
COPY mockbank mockbank
COPY generator generator
COPY schemas schemas
COPY config config
COPY examples examples
COPY docs docs

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "mockbank.app:app", "--host", "0.0.0.0", "--port", "8000"]

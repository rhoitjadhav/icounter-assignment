FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV SQLALCHEMY_DATABASE_URL=sqlite:////data/ip_lookup.db
ENV PYTHONPATH=/app/src

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

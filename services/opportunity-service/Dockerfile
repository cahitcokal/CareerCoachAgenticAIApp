FROM python:3.12-slim

WORKDIR /srv
COPY services/shared /srv/shared
COPY services/opportunity-service /srv/opportunity-service
RUN pip install --no-cache-dir -r /srv/opportunity-service/requirements.txt
ENV PYTHONPATH=/srv/shared
WORKDIR /srv/opportunity-service
EXPOSE 8004
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8004}"]

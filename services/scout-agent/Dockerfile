FROM python:3.12-slim

WORKDIR /srv
COPY services/shared /srv/shared
COPY services/scout-agent /srv/scout-agent
RUN pip install --no-cache-dir -r /srv/scout-agent/requirements.txt
ENV PYTHONPATH=/srv/shared
WORKDIR /srv/scout-agent
EXPOSE 8005
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8005}"]

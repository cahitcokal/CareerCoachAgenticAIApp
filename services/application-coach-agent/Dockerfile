FROM python:3.12-slim

WORKDIR /srv
COPY services/shared /srv/shared
COPY services/application-coach-agent /srv/application-coach-agent
RUN pip install --no-cache-dir -r /srv/application-coach-agent/requirements.txt
ENV PYTHONPATH=/srv/shared
WORKDIR /srv/application-coach-agent
EXPOSE 8007
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8007}"]

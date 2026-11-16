FROM python:3.12-slim

WORKDIR /srv
COPY services/shared /srv/shared
COPY services/relocation-agent /srv/relocation-agent
RUN pip install --no-cache-dir -r /srv/relocation-agent/requirements.txt
ENV PYTHONPATH=/srv/shared
WORKDIR /srv/relocation-agent
EXPOSE 8006
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8006}"]

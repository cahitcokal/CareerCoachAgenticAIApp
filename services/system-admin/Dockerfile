FROM python:3.12-slim

WORKDIR /srv
COPY services/shared /srv/shared
COPY services/system-admin /srv/system-admin
RUN pip install --no-cache-dir -r /srv/system-admin/requirements.txt
ENV PYTHONPATH=/srv/shared
WORKDIR /srv/system-admin
EXPOSE 8003
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8003}"]

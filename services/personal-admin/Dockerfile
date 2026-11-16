FROM python:3.12-slim

WORKDIR /srv
COPY services/shared /srv/shared
COPY services/personal-admin /srv/personal-admin
RUN pip install --no-cache-dir -r /srv/personal-admin/requirements.txt
ENV PYTHONPATH=/srv/shared
WORKDIR /srv/personal-admin
EXPOSE 8002
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8002}"]

FROM python:3.12-slim

WORKDIR /srv
COPY services/shared /srv/shared
COPY services/user-management /srv/user-management
RUN pip install --no-cache-dir -r /srv/user-management/requirements.txt
ENV PYTHONPATH=/srv/shared
WORKDIR /srv/user-management
EXPOSE 8001
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]

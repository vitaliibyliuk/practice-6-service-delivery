FROM python:3.13-slim-bookworm@sha256:a5a7017efc5969e00ae2b91c8eb0631049a569652aa4ffc4501769049ae45c72
WORKDIR /opt/monitor
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY monitor.py gunicorn.conf.py ./
ARG RELEASE_ID=workbench
ENV RELEASE_ID=${RELEASE_ID} \
    READINESS=ready \
    SERVICE_PORT=8100 \
    PYTHONDONTWRITEBYTECODE=1
USER 11020:11020
EXPOSE 8100
ENTRYPOINT ["gunicorn", "--config", "gunicorn.conf.py", "monitor:create_app()"]

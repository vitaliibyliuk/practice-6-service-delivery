import os
import re

from flask import Flask, jsonify


def port_from_environment():
    raw = os.environ.get("SERVICE_PORT", "8100")
    if not raw.isdecimal() or not 1024 <= int(raw) <= 65535:
        raise ValueError("SERVICE_PORT must be an integer from 1024 to 65535")
    return int(raw)


def create_app():
    release = os.environ.get("RELEASE_ID", "workbench")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", release):
        raise ValueError("RELEASE_ID must contain 1–64 valid version characters")

    readiness = os.environ.get("READINESS", "ready")
    if readiness not in {"ready", "offline"}:
        raise ValueError("READINESS must be ready or offline")

    app = Flask(__name__)
    app.config.update(RELEASE_ID=release, READINESS=readiness, SERVICE_PORT=port_from_environment())

    @app.get("/health")
    def health():
        ready = app.config["READINESS"] == "ready"
        return jsonify(ready=ready), 200 if ready else 503

    @app.get("/version")
    def version():
        return jsonify(revision=app.config["RELEASE_ID"])

    return app

import pytest

from monitor import create_app


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("SERVICE_PORT", "8100")
    monkeypatch.setenv("RELEASE_ID", "lab.12")
    monkeypatch.setenv("READINESS", "ready")
    return create_app


@pytest.mark.parametrize(
    ("path", "expected"),
    [("/health", {"ready": True}), ("/version", {"revision": "lab.12"})],
)
def test_public_json(configured, path, expected):
    result = configured().test_client().get(path)
    assert result.status_code == 200
    assert result.json == expected


def test_offline_response(configured, monkeypatch):
    monkeypatch.setenv("READINESS", "offline")
    result = configured().test_client().get("/health")
    assert result.status_code == 503
    assert result.json == {"ready": False}


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("SERVICE_PORT", "NaN"),
        ("SERVICE_PORT", "80"),
        ("SERVICE_PORT", "65536"),
        ("RELEASE_ID", " "),
        ("RELEASE_ID", "invalid/tag"),
        ("READINESS", "broken"),
    ],
)
def test_rejects_bad_environment(configured, monkeypatch, variable, value):
    monkeypatch.setenv(variable, value)
    with pytest.raises(ValueError, match=variable):
        configured()

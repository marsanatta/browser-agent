"""Token gate on the public agent endpoints.

Uses /screenshots/<missing>.png as the probe: the middleware short-circuits
before routing, so a blocked request is 401/503 and an allowed one falls through
to StaticFiles' 404 — cleanly distinguishing 'gate blocked' from 'gate passed'
without running the agent loop.
"""

from fastapi.testclient import TestClient

from app.main import app

PROBE = "/screenshots/does-not-exist.png"
SECRET = "s3cret-token-value"


def _client():
    return TestClient(app)


def test_protected_503_when_unconfigured(monkeypatch):
    monkeypatch.delenv("AGENT_ACCESS_TOKEN", raising=False)
    assert _client().get(PROBE).status_code == 503


def test_protected_401_without_token(monkeypatch):
    monkeypatch.setenv("AGENT_ACCESS_TOKEN", SECRET)
    assert _client().get(PROBE).status_code == 401


def test_protected_401_with_wrong_token(monkeypatch):
    monkeypatch.setenv("AGENT_ACCESS_TOKEN", SECRET)
    assert _client().get(PROBE, params={"token": "nope"}).status_code == 401


def test_passes_with_query_token(monkeypatch):
    monkeypatch.setenv("AGENT_ACCESS_TOKEN", SECRET)
    assert _client().get(PROBE, params={"token": SECRET}).status_code == 404


def test_passes_with_bearer(monkeypatch):
    monkeypatch.setenv("AGENT_ACCESS_TOKEN", SECRET)
    r = _client().get(PROBE, headers={"Authorization": f"Bearer {SECRET}"})
    assert r.status_code == 404


def test_health_open_without_token(monkeypatch):
    monkeypatch.setenv("AGENT_ACCESS_TOKEN", SECRET)
    assert _client().get("/health").status_code == 200


def test_auth_endpoint_sets_cookie_and_authorizes(monkeypatch):
    monkeypatch.setenv("AGENT_ACCESS_TOKEN", SECRET)
    c = _client()
    assert c.get(PROBE).status_code == 401  # no cookie yet
    ok = c.post("/auth", json={"token": SECRET})
    assert ok.status_code == 200
    assert "agent_token" in ok.cookies
    # cookie now rides along automatically (as SSE/img would)
    assert c.get(PROBE).status_code == 404


def test_auth_endpoint_rejects_bad_token(monkeypatch):
    monkeypatch.setenv("AGENT_ACCESS_TOKEN", SECRET)
    assert _client().post("/auth", json={"token": "wrong"}).status_code == 401


def test_auth_endpoint_503_when_unconfigured(monkeypatch):
    monkeypatch.delenv("AGENT_ACCESS_TOKEN", raising=False)
    assert _client().post("/auth", json={"token": "anything"}).status_code == 503

from biomni.tool import database


class _FakeResponse:
    text = '{"ok": true}'

    def raise_for_status(self):
        return None

    def json(self):
        return {"ok": True}


def test_query_rest_api_uses_default_timeout(monkeypatch):
    captured = {}

    def fake_get(endpoint, params=None, headers=None, timeout=None):
        captured["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setattr(database.requests, "get", fake_get)
    result = database._query_rest_api(endpoint="https://example.org/api", method="GET")

    assert result["success"] is True
    assert captured["timeout"] == database.DEFAULT_HTTP_TIMEOUT
    assert result["query_info"]["timeout"] == database.DEFAULT_HTTP_TIMEOUT


def test_query_rest_api_respects_explicit_timeout(monkeypatch):
    captured = {}
    custom_timeout = (1, 2)

    def fake_get(endpoint, params=None, headers=None, timeout=None):
        captured["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setattr(database.requests, "get", fake_get)
    result = database._query_rest_api(endpoint="https://example.org/api", method="GET", timeout=custom_timeout)

    assert result["success"] is True
    assert captured["timeout"] == custom_timeout
    assert result["query_info"]["timeout"] == custom_timeout

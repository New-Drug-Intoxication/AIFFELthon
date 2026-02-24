from biomni.tool import database


def test_query_ensembl_timeout_returns_structured_error(monkeypatch):
    """Timeout from underlying HTTP request should be normalized to ENSEMBL_TIMEOUT."""

    def fake_query_rest_api(endpoint, method="GET", params=None, headers=None, json_data=None, description=None, timeout=None):
        return {
            "success": False,
            "error": "Read timed out while connecting to Ensembl",
            "query_info": {
                "endpoint": endpoint,
                "method": method,
                "description": description,
            },
        }

    monkeypatch.setattr(database, "_query_rest_api", fake_query_rest_api)

    result = database.query_ensembl(endpoint="/info/assembly/homo_sapiens/21", verbose=False)
    assert result["success"] is False
    assert result["error"].startswith("ENSEMBL_TIMEOUT:")
    assert "result_raw" in result


def test_query_ensembl_cache_hit_reuses_previous_result(monkeypatch):
    """Repeated identical Ensembl query should hit tool cache and return cached metadata."""
    count = {"n": 0}

    def fake_query_rest_api(endpoint, method="GET", params=None, headers=None, json_data=None, description=None, timeout=None):
        count["n"] += 1
        return {
            "success": True,
            "query_info": {
                "endpoint": endpoint,
                "method": method,
                "description": description,
                "timeout": timeout,
            },
            "result": {"x": 1},
        }

    monkeypatch.setattr(database, "_query_rest_api", fake_query_rest_api)

    first = database.query_ensembl(endpoint="/info/assembly/homo_sapiens/21", verbose=False)
    second = database.query_ensembl(endpoint="/info/assembly/homo_sapiens/21", verbose=False)

    assert first["success"] is True
    assert second["success"] is True
    assert first["query_info"].get("cache_hit") is False
    assert second["query_info"].get("cache_hit") is True
    assert count["n"] == 1

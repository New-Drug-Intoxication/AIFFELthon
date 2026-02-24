from biomni.tool import database


def test_query_monarch_timeout_returns_structured_error(monkeypatch):
    def fake_query_rest_api(endpoint, method="GET", params=None, headers=None, json_data=None, description=None):
        return {
            "success": False,
            "error": "Read timed out while connecting to monarch",
            "query_info": {
                "endpoint": endpoint,
                "method": method,
                "description": description,
            },
        }

    def fake_llm_result(prompt, schema, system_template):
        return {
            "success": True,
            "data": {
                "url": "https://api.monarchinitiative.org/v3/api/search?q=breast%20cancer&category=biolink:Disease",
                "params": {"q": "breast cancer"},
                "description": "Monarch test",
            },
        }

    monkeypatch.setattr(database, "_query_rest_api", fake_query_rest_api)
    monkeypatch.setattr(database, "_query_llm_for_api", fake_llm_result)

    result = database.query_monarch(prompt="breast cancer", verbose=False)
    assert result["success"] is False
    assert result["error"].startswith("MONARCH_TIMEOUT:")
    assert "result_raw" in result


def test_query_monarch_enforces_limit_with_build_request(monkeypatch):
    captured = {}

    def fake_query_rest_api(endpoint, method="GET", params=None, headers=None, json_data=None, description=None):
        captured["endpoint"] = endpoint
        captured["params"] = params or {}
        return {
            "success": True,
            "query_info": {
                "endpoint": endpoint,
                "method": method,
                "description": description,
            },
            "result": {"_links": {}, "_embedded": {"results": [1, 2]}, "page": {"size": 2}},
        }

    def fake_llm_result(prompt, schema, system_template):
        return {
            "success": True,
            "data": {
                "url": "https://api.monarchinitiative.org/v3/api/search?q=breast%20cancer&category=biolink:Disease",
                "params": {"q": "breast cancer", "page": "1", "limit": "99"},
                "description": "Monarch test",
            },
        }

    monkeypatch.setattr(database, "_query_rest_api", fake_query_rest_api)
    monkeypatch.setattr(database, "_query_llm_for_api", fake_llm_result)

    result = database.query_monarch(prompt="breast cancer", max_results=3, verbose=False)
    assert result["success"] is True
    assert captured["params"].get("limit") == 3
    assert "size" not in captured["params"]
    assert "rows" not in captured["params"]


def test_query_monarch_summarizes_large_payload(monkeypatch):
    large_payload = {
        "_links": {"self": {"href": "..."}},
        "_embedded": {
            "results": [
                {"id": i, "name": f"item-{i}"}
                for i in range(30)
            ]
        },
        "page": {"totalElements": 30, "size": 30},
    }

    def fake_query_rest_api(endpoint, method="GET", params=None, headers=None, json_data=None, description=None):
        return {
            "success": True,
            "query_info": {
                "endpoint": endpoint,
                "method": method,
                "description": description,
            },
            "result": large_payload,
        }

    def fake_llm_result(prompt, schema, system_template):
        return {
            "success": True,
            "data": {
                "url": "https://api.monarchinitiative.org/v3/api/search?q=breast%20cancer&category=biolink:Disease",
                "params": {"q": "breast cancer"},
                "description": "Monarch test",
            },
        }

    monkeypatch.setattr(database, "_query_rest_api", fake_query_rest_api)
    monkeypatch.setattr(database, "_query_llm_for_api", fake_llm_result)

    result = database.query_monarch(prompt="breast cancer", max_results=5, verbose=False)
    assert result["success"] is True
    assert result["result"]["_links"]["self"]["href"] == "..."
    assert result["result"]["results"]["summary"]["truncated"] is True
    assert result["result"]["results"]["summary"]["returned"] == 5
    assert result["result"]["results"]["summary"]["total"] == 30
    assert "result_raw" in result


from biomni.tool import database


def test_query_gwas_catalog_uses_gwas_env_timeouts(monkeypatch):
    monkeypatch.setenv("BIOMNI_GWAS_CONNECT_TIMEOUT", "2")
    monkeypatch.setenv("BIOMNI_GWAS_READ_TIMEOUT", "4")

    captured = {}

    def fake_query_rest_api(endpoint, method, params, description, timeout):
        captured["endpoint"] = endpoint
        captured["method"] = method
        captured["params"] = params
        captured["timeout"] = timeout
        return {"success": True, "result": {"test": True}, "query_info": {}}

    monkeypatch.setattr(database, "_query_rest_api", fake_query_rest_api)

    output = database.query_gwas_catalog(endpoint="studies", max_results=5)

    assert output["success"] is True
    assert captured["method"] == "GET"
    assert captured["endpoint"] == "https://www.ebi.ac.uk/gwas/rest/api/studies"
    assert captured["timeout"] == (2.0, 4.0)
    assert captured["params"]["size"] == 5


def test_query_gwas_catalog_prompt_branch_enforces_size_and_removes_aliases(monkeypatch):
    captured = {}
    query_info = {
        "endpoint": "studies",
        "params": {"size": 100, "limit": 100, "rows": 100, "pageSize": 100},
        "description": "LLM generated query",
    }

    def fake_query_llm_for_api(*args, **kwargs):
        return {"success": True, "data": query_info}

    def fake_query_rest_api(endpoint, method, params, description, timeout):
        captured["params"] = params
        return {"success": True, "result": {"test": True}, "query_info": {}}

    monkeypatch.setattr(database, "_query_llm_for_api", fake_query_llm_for_api)
    monkeypatch.setattr(database, "_query_rest_api", fake_query_rest_api)

    output = database.query_gwas_catalog(prompt="find type2 diabetes genes", max_results=3)

    assert output["success"] is True
    assert captured["params"]["size"] == 3
    assert "limit" not in captured["params"]
    assert "rows" not in captured["params"]
    assert "pageSize" not in captured["params"]


def test_query_gwas_catalog_sanitizes_projection_and_querystring_params(monkeypatch):
    captured = {}

    def fake_query_rest_api(endpoint, method, params, description, timeout):
        captured["endpoint"] = endpoint
        captured["params"] = params
        captured["method"] = method
        return {"success": True, "result": {"_embedded": {}}, "query_info": {}}

    monkeypatch.setattr(database, "_query_rest_api", fake_query_rest_api)

    output = database.query_gwas_catalog(
        endpoint="associations?projection=bad&page=2&limit=20&rows=20&size=50&query=foo",
        max_results=4,
    )

    assert output["success"] is True
    assert captured["method"] == "GET"
    assert captured["endpoint"] == "https://www.ebi.ac.uk/gwas/rest/api/associations"
    assert captured["params"]["size"] == 4
    assert captured["params"]["page"] == 2
    assert "limit" not in captured["params"]
    assert "rows" not in captured["params"]
    assert "pageSize" not in captured["params"]
    assert "projection" not in captured["params"]
    assert captured["params"]["query"] == "foo"

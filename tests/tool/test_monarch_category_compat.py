from biomni.tool import database


def test_query_monarch_normalizes_legacy_gene_to_disease_category(monkeypatch):
    calls = []

    def fake_llm_for_api(prompt, schema, system_template):
        return {
            "success": True,
            "data": {
                "endpoint": "association_table",
                "url": "https://api.monarchinitiative.org/v3/api/entity/PIEZO2/biolink:GeneToDiseaseAssociation",
                "params": {},
            },
        }

    def fake_query_rest_api(endpoint, method="GET", params=None, headers=None, json_data=None, description=None):
        calls.append(endpoint)
        return {
            "success": True,
            "query_info": {"endpoint": endpoint, "method": method, "description": description},
            "result": {"ok": True},
        }

    monkeypatch.setattr(database, "_query_llm_for_api", fake_llm_for_api)
    monkeypatch.setattr(database, "_query_rest_api", fake_query_rest_api)

    result = database.query_monarch(prompt="Find diseases linked to PIEZO2", verbose=True)
    assert result["success"] is True
    assert calls
    assert "/biolink:CausalGeneToDiseaseAssociation" in calls[0]


def test_query_monarch_retries_with_compatible_category_on_422(monkeypatch):
    calls = []

    def fake_llm_for_api(prompt, schema, system_template):
        return {
            "success": True,
            "data": {
                "endpoint": "association_table",
                "url": "https://api.monarchinitiative.org/v3/api/entity/PIEZO2/biolink:UnknownAssociation",
                "params": {},
            },
        }

    def fake_query_rest_api(endpoint, method="GET", params=None, headers=None, json_data=None, description=None):
        calls.append(endpoint)
        if len(calls) == 1:
            return {
                "success": False,
                "error": "API error: 422 Client Error",
                "response_url_error": '{"detail":[{"type":"enum","input":"biolink:GeneToDiseaseAssociation","msg":"Input should be ..."}]}',
                "query_info": {"endpoint": endpoint, "method": method, "description": description},
            }
        return {
            "success": True,
            "query_info": {"endpoint": endpoint, "method": method, "description": description},
            "result": {"ok": True},
        }

    monkeypatch.setattr(database, "_query_llm_for_api", fake_llm_for_api)
    monkeypatch.setattr(database, "_query_rest_api", fake_query_rest_api)

    result = database.query_monarch(prompt="Find diseases linked to PIEZO2", verbose=True)
    assert result["success"] is True
    assert len(calls) == 2
    assert "/biolink:CausalGeneToDiseaseAssociation" in calls[1]

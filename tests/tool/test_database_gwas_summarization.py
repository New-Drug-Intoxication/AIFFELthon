from biomni.tool import database


def _make_gwas_item(i: int) -> dict:
    return {
        "trait": f"trait-{i}",
        "locus": f"1q{i%3}",
        "pvalueMantissa": i + 1,
        "pvalueExponent": - (i % 8),
        "loci": [
            {
                "strongestRiskAlleles": [
                    {"riskAlleleName": f"rs{i}-?"},
                ],
            },
        ],
    }


def test_query_gwas_catalog_summarizes_large_hal_payload(monkeypatch):
    large_payload = {
        "_embedded": {
            "associations": [_make_gwas_item(i) for i in range(40)],
        },
        "_links": {
            "self": {"href": "https://www.ebi.ac.uk/gwas/rest/api/associations"},
        },
        "page": {"size": 40, "totalElements": 40, "totalPages": 2, "number": 0},
    }

    def fake_query_rest_api(endpoint, method, params, description, timeout):
        return {"success": True, "result": large_payload, "query_info": {"endpoint": endpoint, "method": method}}

    monkeypatch.setattr(database, "_query_rest_api", fake_query_rest_api)

    output = database.query_gwas_catalog(endpoint="associations", max_results=5)

    assert output["success"] is True
    assert output["result"]["_embedded"]["associations"]["summary"]["truncated"] is True
    assert output["result"]["_embedded"]["associations"]["summary"]["total"] == 40
    assert output["result"]["_embedded"]["associations"]["summary"]["returned"] == 5
    assert len(output["result"]["_embedded"]["associations"]["items"]) == 5
    assert output["result"]["_embedded"]["associations"]["items"][0]["trait"] == "trait-0"
    assert output["result"]["_embedded"]["associations"]["items"][0]["snp"] == "rs0"
    assert output["result"]["_embedded"]["associations"]["items"][-1]["snp"] == "rs4"
    assert output["result_summary"]["max_items"] == 5
    assert output["result_summary"]["result_type"] == "gwas_hal_summary"
    assert output["result_raw"] == large_payload

import pandas as pd

from biomni.tool import genomics


def test_get_rna_seq_archs4_includes_timeout_hint_when_timed_out(monkeypatch):
    class DummyGget:
        def archs4(self, _gene_name, which="tissue"):
            return pd.DataFrame([{"id": "liver", "median": 1.0}])

    monkeypatch.setattr(genomics, "_require_gget", lambda: DummyGget())
    monkeypatch.setattr(
        genomics,
        "run_with_timeout",
        lambda func, args=None, kwargs=None, timeout=600: "TIMEOUT: get_rna_seq_archs4 execution timed out",
    )
    genomics._ARCHS4_RESULT_CACHE.clear()

    output = genomics.get_rna_seq_archs4("TP53", K=5)

    assert "TIMEOUT:" in output
    assert "Use fewer genes/iterations" in output


def test_get_rna_seq_archs4_uses_cache_for_repeated_query(monkeypatch):
    calls = {"count": 0}

    class DummyGget:
        def archs4(self, gene_name, which="tissue"):
            calls["count"] += 1
            return pd.DataFrame(
                [
                    {"id": "liver", "median": 1.1},
                    {"id": "brain", "median": 2.2},
                ]
            )

    monkeypatch.setattr(genomics, "_require_gget", lambda: DummyGget())

    def immediate_run(func, args=None, kwargs=None, timeout=600):
        return func()

    monkeypatch.setattr(genomics, "run_with_timeout", immediate_run)
    genomics._ARCHS4_RESULT_CACHE.clear()

    out1 = genomics.get_rna_seq_archs4("TP53", K=2)
    out2 = genomics.get_rna_seq_archs4("TP53", K=2)

    assert calls["count"] == 1
    assert "[cache] Reused cached ArchS4 result" in out2
    assert "Tissue: liver" in out1

import importlib
import builtins


def test_genomics_module_import_does_not_require_gget(monkeypatch):
    genomics = importlib.import_module("biomni.tool.genomics")
    assert hasattr(genomics, "get_rna_seq_archs4")

    monkeypatch.setattr(genomics, "_GGET_MODULE", None, raising=False)
    monkeypatch.setattr(
        genomics,
        "_GGET_IMPORT_ERROR",
        ModuleNotFoundError("No module named 'gget'"),
        raising=False,
    )

    message = genomics.get_rna_seq_archs4("TP53", K=1)
    lowered = message.lower()
    assert "gget" in lowered
    assert "install" in lowered


def test_bioimaging_exposes_registration_visualization_function():
    bioimaging = importlib.import_module("biomni.tool.bioimaging")
    assert hasattr(bioimaging, "create_registration_visualization")


def test_query_scholar_returns_install_hint_when_scholarly_missing(monkeypatch):
    literature = importlib.import_module("biomni.tool.literature")
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "scholarly":
            raise ModuleNotFoundError("No module named 'scholarly'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    message = literature.query_scholar("test query")
    lowered = message.lower()
    assert "scholarly" in lowered
    assert "pip install scholarly" in lowered


def test_database_query_pubmed_alias(monkeypatch):
    database = importlib.import_module("biomni.tool.database")
    literature = importlib.import_module("biomni.tool.literature")

    def fake_query_pubmed(query, max_papers=10, max_retries=3):
        return f"ok:{query}:{max_papers}:{max_retries}"

    monkeypatch.setattr(literature, "query_pubmed", fake_query_pubmed)
    output = database.query_pubmed("abc", max_papers=5, max_retries=2)
    assert output == "ok:abc:5:2"

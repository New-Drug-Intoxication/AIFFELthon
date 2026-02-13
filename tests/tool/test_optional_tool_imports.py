import importlib


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

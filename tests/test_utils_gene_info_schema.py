import pandas as pd

from biomni.utils import normalize_gene_info_schema


def test_normalize_gene_info_schema_adds_compat_alias(tmp_path):
    path = tmp_path / "gene_info.parquet"
    df = pd.DataFrame(
        {
            "gene_id": ["ENSG00000123456", "ENSG00000234567"],
            "gene_name": ["GENE1", "GENE2"],
        }
    )
    df.to_parquet(path)

    result = normalize_gene_info_schema(str(tmp_path))

    assert result.get("ok") is True
    assert result.get("status") == "added_compat_alias"
    assert result.get("alias_from") == "gene_id"

    reloaded = pd.read_parquet(path)
    assert "ensembl_gene_id" in reloaded.columns
    assert (reloaded["ensembl_gene_id"] == reloaded["gene_id"]).all()


def test_normalize_gene_info_schema_already_compatible(tmp_path):
    path = tmp_path / "gene_info.parquet"
    df = pd.DataFrame(
        {
            "ensembl_gene_id": ["ENSG00000123456"],
            "gene_name": ["GENE1"],
        }
    )
    df.to_parquet(path)

    result = normalize_gene_info_schema(str(tmp_path))

    assert result.get("ok") is True
    assert result.get("status") == "already_compatible"


def test_normalize_gene_info_schema_handles_missing_file(tmp_path):
    result = normalize_gene_info_schema(str(tmp_path))
    assert result.get("ok") is False
    assert result.get("status") == "missing_file"

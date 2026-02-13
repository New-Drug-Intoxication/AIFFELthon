from urllib.error import URLError

from biomni.tool import database


def test_blast_sequence_returns_ssl_error_code_and_hint(monkeypatch):
    def fake_qblast(*args, **kwargs):
        raise URLError("[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol")

    monkeypatch.setattr(database.NCBIWWW, "qblast", fake_qblast)
    output = database.blast_sequence("MKTFFVAGVIL", "nr", "blastp")
    assert isinstance(output, str)
    assert output.startswith("BLAST_UNAVAILABLE_SSL:")
    assert "Hint:" in output
    assert "query_uniprot" in output


def test_blast_sequence_returns_timeout_error_code_and_hint(monkeypatch):
    def fake_qblast(*args, **kwargs):
        raise TimeoutError("request timeout while contacting NCBI")

    monkeypatch.setattr(database.NCBIWWW, "qblast", fake_qblast)
    output = database.blast_sequence("MKTFFVAGVIL", "nr", "blastp")
    assert isinstance(output, str)
    assert output.startswith("BLAST_TIMEOUT:")
    assert "query_clinvar" in output

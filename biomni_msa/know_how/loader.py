from __future__ import annotations

import glob
import os
from pathlib import Path


class KnowHowLoader:
    def __init__(self, know_how_dir: str | None = None):
        if know_how_dir is None:
            know_how_dir = str(Path(__file__).parent)
        self.know_how_dir = know_how_dir
        self.documents: dict[str, dict] = {}
        self._load_documents()

    def _load_documents(self) -> None:
        for filepath in glob.glob(os.path.join(self.know_how_dir, "*.md")):
            filename = os.path.basename(filepath)
            stem = os.path.splitext(filename)[0]
            if filename.upper() in {"README.MD", "QUICK_START.MD"} or stem.isupper():
                continue
            content = Path(filepath).read_text(encoding="utf-8")
            title = self._extract_title(content, stem)
            short = self._extract_short_description(content)
            self.documents[stem] = {
                "id": stem,
                "name": title,
                "description": short,
                "content": content,
                "content_without_metadata": self._strip_metadata(content),
                "filepath": filepath,
            }

    @staticmethod
    def _extract_title(content: str, fallback_stem: str) -> str:
        for line in content.splitlines():
            if line.startswith("# "):
                return line[2:].strip() or fallback_stem
        return fallback_stem

    @staticmethod
    def _extract_short_description(content: str) -> str:
        for line in content.splitlines():
            marker = "**Short Description**:"
            if line.startswith(marker):
                return line[len(marker) :].strip()
        return ""

    @staticmethod
    def _strip_metadata(content: str) -> str:
        lines = content.splitlines()
        out: list[str] = []
        in_meta = False
        for line in lines:
            if line.startswith("## Metadata"):
                in_meta = True
                continue
            if in_meta and line.startswith("## "):
                in_meta = False
            if in_meta:
                continue
            out.append(line)
        return "\n".join(out).strip()

    def get_all_documents(self) -> list[dict]:
        return list(self.documents.values())

    def get_document_by_id(self, doc_id: str) -> dict | None:
        return self.documents.get(doc_id)

    def get_document_summaries(self) -> list[dict]:
        return [
            {
                "id": doc["id"],
                "name": doc["name"],
                "description": doc["description"],
            }
            for doc in self.documents.values()
        ]

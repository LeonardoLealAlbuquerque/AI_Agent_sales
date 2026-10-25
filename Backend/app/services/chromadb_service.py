import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable

import chromadb
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from langchain_text_splitters import MarkdownHeaderTextSplitter

DEFAULT_PLAYBOOK_PATH = "docs/playbook_negociacao_b2b.md"
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class KnowledgeBaseNotReadyError(RuntimeError):
    """Raised when the playbook index is missing or out of date."""


class ChromaDBService:
    def __init__(
        self,
        persist_directory: str | Path | None = None,
        collection_name: str = "kb_playbook",
        embedding_function: Callable[..., Any] | None = None,
    ) -> None:
        configured_directory = persist_directory or os.getenv(
            "CHROMA_PERSIST_DIRECTORY", str(BACKEND_ROOT / "data" / "chroma")
        )
        persist_path = Path(configured_directory)
        if not persist_path.is_absolute():
            persist_path = BACKEND_ROOT / persist_path
        self.persist_directory = str(persist_path.resolve())
        self.collection_name = collection_name
        self.embedding_function = (
            embedding_function or ONNXMiniLM_L6_V2()
        )
        self._source_path: Path | None = None

        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_function,
        )

    def _resolve_playbook_path(self, file_path: str | Path) -> Path:
        path = Path(file_path)
        if path.is_absolute():
            resolved_path = path
        else:
            resolved_path = BACKEND_ROOT / path

        if not resolved_path.is_file():
            raise FileNotFoundError(
                f"Playbook não encontrado: {resolved_path.name}"
            )
        return resolved_path.resolve()

    def _load_markdown_utf8(self, file_path: str | Path) -> tuple[Path, str]:
        source_path = self._resolve_playbook_path(file_path)
        return source_path, source_path.read_text(encoding="utf-8")

    @staticmethod
    def _split_playbook(content: str, source_name: str) -> tuple[list[str], list[dict[str, str]], list[str]]:
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header_1"),
                ("##", "Header_2"),
                ("###", "Header_3"),
            ],
            strip_headers=False,
        )
        splits = splitter.split_text(content)

        documents: list[str] = []
        metadatas: list[dict[str, str]] = []
        ids: list[str] = []

        for index, split in enumerate(splits):
            chunk_text = split.page_content.strip()
            if not chunk_text:
                continue

            metadata = {
                key: str(value)
                for key, value in split.metadata.items()
            }
            section = (
                metadata.get("Header_3")
                or metadata.get("Header_2")
                or metadata.get("Header_1")
                or "Geral"
            )
            metadata.update({"source": source_name, "section": section})
            chunk_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()

            documents.append(chunk_text)
            metadatas.append(metadata)
            ids.append(f"playbook_{index}_{chunk_hash}")

        return documents, metadatas, ids

    def get_status(
        self, file_path: str | Path | None = None
    ) -> dict[str, Any]:
        selected_path = file_path or self._source_path or DEFAULT_PLAYBOOK_PATH
        try:
            source_path, content = self._load_markdown_utf8(selected_path)
        except FileNotFoundError:
            return {
                "status": "not_ready",
                "reason": "playbook_missing",
                "message": "O arquivo do playbook não foi encontrado.",
                "chunks_count": self.collection.count(),
            }

        source_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        chunks_count = self.collection.count()
        indexed_hash = (self.collection.metadata or {}).get("playbook_sha256")

        if chunks_count == 0:
            return {
                "status": "not_ready",
                "reason": "index_empty",
                "message": "O playbook ainda não foi ingerido.",
                "chunks_count": 0,
            }

        if indexed_hash != source_hash:
            return {
                "status": "not_ready",
                "reason": "index_stale",
                "message": "O índice não corresponde à versão atual do playbook.",
                "chunks_count": chunks_count,
            }

        return {
            "status": "ready",
            "source": source_path.name,
            "chunks_count": chunks_count,
        }

    def ingest_playbook(
        self,
        file_path: str | Path = DEFAULT_PLAYBOOK_PATH,
        force_recreate: bool = False,
    ) -> dict[str, Any]:
        source_path, content = self._load_markdown_utf8(file_path)
        self._source_path = source_path
        documents, metadatas, ids = self._split_playbook(
            content, source_path.name
        )
        if not documents:
            raise ValueError("O playbook não contém fragmentos válidos para ingestão.")

        source_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        existing = self.collection.get(include=["metadatas"])
        existing_ids = set(existing["ids"])
        indexed_hash = (self.collection.metadata or {}).get("playbook_sha256")

        if (
            not force_recreate
            and indexed_hash == source_hash
            and existing_ids == set(ids)
        ):
            return {
                "status": "skipped",
                "message": "O índice já corresponde à versão atual do playbook.",
                "chunks_count": len(ids),
            }

        if force_recreate:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
                embedding_function=self.embedding_function,
            )

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        refreshed_ids = set(
            self.collection.get(include=["metadatas"])["ids"]
        )
        stale_ids = refreshed_ids - set(ids)
        if stale_ids:
            self.collection.delete(ids=sorted(stale_ids))

        self.collection.modify(
            metadata={
                "hnsw:space": "cosine",
                "playbook_sha256": source_hash,
            }
        )

        return {
            "status": "success",
            "message": "Ingestão do playbook concluída.",
            "chunks_count": len(ids),
        }

    def search_similarity(
        self,
        query: str,
        n_results: int = 3,
        file_path: str | Path | None = None,
    ) -> list[dict[str, Any]]:
        if not query or not query.strip():
            raise ValueError(
                "O parâmetro 'query' de busca é obrigatório e não pode ser vazio."
            )

        status = self.get_status(file_path)
        if status["status"] != "ready":
            raise KnowledgeBaseNotReadyError(status["message"])

        top_k = max(1, min(n_results, 10, status["chunks_count"]))
        try:
            results = self.collection.query(
                query_texts=[query.strip()],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise RuntimeError("Falha ao consultar o índice do playbook.") from exc

        documents = results.get("documents") or [[]]
        if not documents or not documents[0]:
            return []

        metadatas = results.get("metadatas") or [[]]
        distances = results.get("distances") or [[]]
        return [
            {
                "content": document,
                "metadata": (
                    metadatas[0][index]
                    if metadatas and metadatas[0]
                    else {}
                ),
                "distance": (
                    distances[0][index]
                    if distances and distances[0]
                    else None
                ),
            }
            for index, document in enumerate(documents[0])
        ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingere o playbook B2B na coleção vetorial local."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recria a coleção antes da ingestão.",
    )
    args = parser.parse_args()

    service = ChromaDBService()
    result = service.ingest_playbook(force_recreate=args.force)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

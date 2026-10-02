import os
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from langchain_text_splitters import MarkdownHeaderTextSplitter

class ChromaDBService:
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "kb_playbook"
    ):
        # Persistência configurável fora do código-fonte (RAG-FR-002)
        self.persist_directory = persist_directory or os.getenv(
            "CHROMA_PERSIST_DIRECTORY", "./data/chroma"
        )
        self.collection_name = collection_name
        
        # Garante a criação do diretório físico no disco
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Cliente persistente do ChromaDB
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def _load_markdown_utf8(self, file_path: str) -> str:
        candidate_paths = [
            Path(file_path),
            Path(__file__).resolve().parent.parent / file_path,         
            Path(__file__).resolve().parent.parent.parent / file_path,   
            Path(__file__).resolve().parent.parent.parent.parent / file_path 
        ]

        target_path = None
        for p in candidate_paths:
            if p.exists() and p.is_file():
                target_path = p
                break

        if not target_path:
            raise FileNotFoundError(
                f"Arquivo da KB não encontrado. Tentou em: {[str(p) for p in candidate_paths]}"
            )

        with open(target_path, "r", encoding="utf-8") as f:
            return f.read()
        
    def ingest_playbook(
        self, 
        file_path: str = "docs/playbook_negociacao_b2b.md", 
        force_recreate: bool = False
    ) -> Dict[str, Any]:
        """
        Realiza a ingestão idempotente do Playbook no ChromaDB.
        - force_recreate=True: Permite recriação controlada da coleção.
        - Não afeta nem altera dados do banco relacional/domínio.
        """
        if force_recreate:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

        # Idempotência: Se a coleção já possui dados e não foi forçada a recriação, ignora reingestão
        existing_count = self.collection.count()
        if existing_count > 0 and not force_recreate:
            return {
                "status": "skipped",
                "message": f"Coleção já alimentada ({existing_count} chunks). Ingestão ignorada.",
                "chunks_count": existing_count
            }

        content = self._load_markdown_utf8(file_path)

        # Fatiamento respeitando os níveis de título Markdown
        headers_to_split_on = [
            ("#", "Header_1"),
            ("##", "Header_2"),
            ("###", "Header_3"),
        ]
        
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False
        )
        splits = markdown_splitter.split_text(content)

        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []

        for i, split in enumerate(splits):
            chunk_text = split.page_content.strip()
            
            # Validação de fragmentos vazios (RAG-FR-005)
            if not chunk_text:
                continue

            # Extração da seção para o metadado
            section = (
                split.metadata.get("Header_2") 
                or split.metadata.get("Header_1") 
                or "Geral"
            )

            metadata = {
                "source": str(file_path),
                "section": str(section),
                **{k: str(v) for k, v in split.metadata.items()}
            }

            # Geração de ID determinístico baseado no índice e hash do texto
            text_hash = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()[:8]
            chunk_id = f"playbook_chunk_{i}_{text_hash}"

            documents.append(chunk_text)
            metadatas.append(metadata)
            ids.append(chunk_id)

        if not documents:
            return {
                "status": "warning",
                "message": "Nenhum fragmento válido extraído.",
                "chunks_count": 0
            }

        # Operação de Upsert garante que a ingestão seja totalmente idempotente
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        return {
            "status": "success",
            "message": "Ingestão executada com sucesso.",
            "chunks_count": len(documents)
        }

    def search_similarity(
            self, 
            query: str, 
            n_results: int = 3
        ) -> List[Dict[str, Any]]:
            """
            Realiza a busca por similaridade semântica na KB (RAG-FR-003, RAG-FR-004).
            - Valida a consulta obrigatória.
            - Limita o top_k (entre 1 e 10).
            - Retorna conteúdo, metadados e distâncias.
            - Trata erros de indisponibilidade da KB.
            """
            if not query or not query.strip():
                raise ValueError("O parâmetro 'query' de busca é obrigatório e não pode ser vazio.")

            # Limita o top_k para evitar estouro de contexto no LLM
            top_k = max(1, min(n_results, 10))

            try:
                if self.collection.count() == 0:
                    return []

                results = self.collection.query(
                    query_texts=[query.strip()],
                    n_results=top_k,
                    include=["documents", "metadatas", "distances"]
                )

                formatted_results = []
                if results and results.get("documents") and results["documents"][0]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                    dists = results["distances"][0] if results.get("distances") else [None] * len(docs)

                    for doc, meta, dist in zip(docs, metas, dists):
                        formatted_results.append({
                            "content": doc,
                            "metadata": meta,
                            "distance": dist
                        })

                return formatted_results

            except Exception as e:
                raise RuntimeError(f"Base de Conhecimento (KB) indisponível: {str(e)}")
        
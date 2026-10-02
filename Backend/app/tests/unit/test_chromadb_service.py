import os
import pytest
from app.services.chromadb_service import ChromaDBService


@pytest.fixture
def test_markdown_file(tmp_path):
    """Cria um arquivo Markdown temporário simulando a estrutura do Playbook B2B."""
    md_content = """# Playbook de Negociação B2B
## 1. Diretrizes Gerais
Esta é a seção inicial com orientações gerais de atendimento.

### Subseção Sem Conteúdo Útil
   

### 2. Descontos e Alçada Decisória
O assistente opera sob alçada zero para concessão de descontos e parcelamentos.
Qualquer exceção exige aprovação da gerência.
"""
    file_path = tmp_path / "test_playbook.md"
    file_path.write_text(md_content, encoding="utf-8")
    return str(file_path)


@pytest.fixture
def chroma_service(tmp_path):
    """Instancia o ChromaDBService isolado em um diretório temporário para os testes."""
    test_dir = str(tmp_path / "chroma_test_db")
    service = ChromaDBService(
        persist_directory=test_dir,
        collection_name="test_kb_collection"
    )
    return service


def test_chromadb_persistence_configuration(tmp_path):
    """Testa se a persistência configurada cria o diretório físico correto (RAG-FR-002)."""
    custom_dir = str(tmp_path / "custom_chroma_path")
    service = ChromaDBService(
        persist_directory=custom_dir, 
        collection_name="test_persist_collection"
    )
    assert os.path.exists(custom_dir)
    assert service.collection_name == "test_persist_collection"


def test_ingest_playbook_headers_metadata_and_non_empty_chunks(chroma_service, test_markdown_file):
    """Testa a leitura por cabeçalhos, validação de fragmentos não vazios e extração de metadados."""
    result = chroma_service.ingest_playbook(file_path=test_markdown_file)
    
    assert result["status"] == "success"
    assert result["chunks_count"] > 0

    # Busca semântica para validar metadados e separação por seções
    search_results = chroma_service.search_similarity(query="alçada zero para descontos", n_results=5)
    assert len(search_results) > 0

    top_result = search_results[0]
    assert "content" in top_result
    assert "metadata" in top_result
    
    # Valida metadados obrigatórios de origem e seção
    assert top_result["metadata"]["source"] == test_markdown_file
    assert "section" in top_result["metadata"]
    assert top_result["metadata"]["section"] != ""


def test_ingest_idempotency_and_force_recreate(chroma_service, test_markdown_file):
    """Testa a ingestão idempotente (skip na 2ª execução) e a recriação forçada com force_recreate."""
    # 1ª execução: deve ingerir com sucesso
    res1 = chroma_service.ingest_playbook(file_path=test_markdown_file)
    assert res1["status"] == "success"
    initial_chunks = res1["chunks_count"]

    # 2ª execução sem forçar recriação: deve ser ignorada (idempotência)
    res2 = chroma_service.ingest_playbook(file_path=test_markdown_file, force_recreate=False)
    assert res2["status"] == "skipped"
    assert res2["chunks_count"] == initial_chunks
    assert "já alimentada" in res2["message"].lower()

    # 3ª execução com recriação forçada: deve limpar a coleção e reingerir
    res3 = chroma_service.ingest_playbook(file_path=test_markdown_file, force_recreate=True)
    assert res3["status"] == "success"
    assert res3["chunks_count"] == initial_chunks


def test_search_similarity_empty_collection(tmp_path):
    """Garante resiliência ao executar busca em uma coleção que ainda não possui documentos."""
    test_dir = str(tmp_path / "empty_chroma_db")
    service = ChromaDBService(persist_directory=test_dir, collection_name="empty_collection")
    results = service.search_similarity(query="qualquer termo de busca")
    assert results == []
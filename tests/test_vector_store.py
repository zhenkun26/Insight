from __future__ import annotations

import sys
import types

from app.models.domain import Chunk
from app.retrieval.vector import MilvusVectorStore


def test_milvus_adapter_contract_with_fake_client(monkeypatch):
    class FakeClient:
        def __init__(self, _uri):
            self.collections = set()
            self.rows = []

        def has_collection(self, name):
            return name in self.collections

        def create_collection(self, **kwargs):
            self.collections.add(kwargs["collection_name"])

        def upsert(self, *, collection_name, data):
            assert collection_name in self.collections
            self.rows = list(data)

        def load_collection(self, *, collection_name):
            assert collection_name in self.collections

        def search(self, *, collection_name, data, limit, output_fields):
            assert collection_name in self.collections
            assert data and output_fields
            return [
                [
                    {
                        "id": row["chunk_id"],
                        "distance": 0.9,
                        "entity": row,
                    }
                    for row in self.rows[:limit]
                ]
            ]

        def delete(self, *, collection_name, filter):
            assert collection_name in self.collections
            document_id = filter.split('"')[1]
            self.rows = [row for row in self.rows if row["document_id"] != document_id]

    fake_module = types.ModuleType("pymilvus")
    fake_module.MilvusClient = FakeClient
    monkeypatch.setitem(sys.modules, "pymilvus", fake_module)

    store = MilvusVectorStore("fake-uri", "test-collection")
    chunk = Chunk("chunk-1", "doc-1", "guide.txt", "台风预警", position=0)
    store.upsert([chunk], [[1.0, 0.0]])
    results = store.search([1.0, 0.0], 1)
    assert results[0].chunk.chunk_id == "chunk-1"
    assert results[0].vector_score == 0.9
    store.delete_document("doc-1")
    assert store.search([1.0, 0.0], 1) == []

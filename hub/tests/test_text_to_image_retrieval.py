"""
hub/tests/test_text_to_image_retrieval.py

Phase 9 / Slice 7C — text->image retrieval path: ranking, floor, top-N,
determinism, and filter/validation gating (S7C.5/7/8). CLIP encoder is stubbed;
embeddings are seeded directly in the DB.
"""

import unittest

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hub.db.session import Base
from hub.db import schema
from hub.retrieval import search
from hub.retrieval import image_embedder as ie
from hub.retrieval.embedder import serialize_embedding


class _StubEmbedder:
    model_version = ie.MODEL_VERSION

    def __init__(self, qvec):
        self.qvec = np.array(qvec, dtype=np.float32)

    def embed_text(self, text):
        return self.qvec


class ImageRetrievalBase(unittest.TestCase):
    def setUp(self):
        e = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(e)
        self.db = sessionmaker(bind=e)()
        self._n = 0

    def tearDown(self):
        self.db.close()

    def _img(self, vec, status="ready", enabled=1, model=ie.MODEL_VERSION, has_emb=True):
        self._n += 1
        asset = schema.ImageAsset(
            content_hash=f"hash{self._n}",
            status=status,
            embedding=serialize_embedding(np.array(vec, dtype=np.float32)) if has_emb else None,
            embedding_model=model if has_emb else None,
        )
        self.db.add(asset)
        self.db.flush()
        item = schema.KBItem(
            question=f"img{self._n}", answer="(image)", modality="image",
            image_asset_id=asset.id, enabled=enabled, created_at=0, last_updated=0,
        )
        self.db.add(item)
        self.db.commit()
        return item, asset


class TestRetrievalRankingAndFloor(ImageRetrievalBase):
    def test_ranks_by_similarity_and_applies_floor(self):
        a, _ = self._img([1.0, 0.0, 0.0])     # sim 1.0 to query
        b, _ = self._img([0.9, 0.1, 0.0])     # high
        c, _ = self._img([0.0, 1.0, 0.0])     # sim ~0 -> below floor
        res = search.retrieve_images(self.db, "the building", floor=0.26, top_n=3,
                                     embedder=_StubEmbedder([1.0, 0.0, 0.0]))
        ids = [r["source_id"] for r in res]
        self.assertEqual(ids, [a.id, b.id])    # c withheld below floor
        self.assertEqual(res[0]["rank"], 1)
        self.assertEqual(res[0]["modality"], "image")
        self.assertTrue(res[0]["render_ref"].startswith("/assets/"))

    def test_top_n_limit(self):
        for _ in range(5):
            self._img([1.0, 0.0, 0.0])
        res = search.retrieve_images(self.db, "x", floor=0.1, top_n=3,
                                     embedder=_StubEmbedder([1.0, 0.0, 0.0]))
        self.assertEqual(len(res), 3)

    def test_tie_break_by_source_id(self):
        a, _ = self._img([1.0, 0.0, 0.0])
        b, _ = self._img([1.0, 0.0, 0.0])  # identical sim -> tie
        res = search.retrieve_images(self.db, "x", floor=0.1, top_n=5,
                                     embedder=_StubEmbedder([1.0, 0.0, 0.0]))
        self.assertEqual([r["source_id"] for r in res], [a.id, b.id])  # asc id

    def test_deterministic(self):
        self._img([1.0, 0.0, 0.0]); self._img([0.8, 0.2, 0.0])
        stub = _StubEmbedder([1.0, 0.0, 0.0])
        r1 = search.retrieve_images(self.db, "x", embedder=stub)
        r2 = search.retrieve_images(self.db, "x", embedder=stub)
        self.assertEqual([(r["source_id"], r["score"]) for r in r1],
                         [(r["source_id"], r["score"]) for r in r2])

    def test_empty_when_no_images(self):
        self.assertEqual(search.retrieve_images(self.db, "x", embedder=_StubEmbedder([1, 0, 0])), [])


class TestRetrievalGates(ImageRetrievalBase):
    def _q(self):
        return search.retrieve_images(self.db, "x", floor=0.1, top_n=10,
                                      embedder=_StubEmbedder([1.0, 0.0, 0.0]))

    def test_excludes_non_ready_asset(self):
        self._img([1.0, 0.0, 0.0], status="pending")
        self._img([1.0, 0.0, 0.0], status="rejected")
        self.assertEqual(self._q(), [])

    def test_excludes_missing_embedding(self):
        self._img([1.0, 0.0, 0.0], has_emb=False)
        self.assertEqual(self._q(), [])

    def test_excludes_stale_model_embedding(self):
        self._img([1.0, 0.0, 0.0], model="old-model-v0")
        self.assertEqual(self._q(), [])

    def test_excludes_disabled_item(self):
        self._img([1.0, 0.0, 0.0], enabled=0)
        self.assertEqual(self._q(), [])

    def test_ready_current_passes(self):
        a, _ = self._img([1.0, 0.0, 0.0])
        self.assertEqual([r["source_id"] for r in self._q()], [a.id])


if __name__ == "__main__":
    unittest.main()

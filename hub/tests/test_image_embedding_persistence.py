"""
hub/tests/test_image_embedding_persistence.py

Phase 9 / Slice 7C — persist image embeddings with model + KB-version metadata,
readiness gating, and model-change invalidation (S7C.3/4). Encoder is a stub.
"""

import io
import os
import tempfile
import unittest

import numpy as np
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hub.db.session import Base
from hub.db import schema
from hub.services import image_assets as ia
from hub.retrieval import image_embedder as ie
from hub.retrieval.embedder import deserialize_embedding


class _StubEmbedder:
    model_version = ie.MODEL_VERSION

    def embed_image(self, image):
        return np.arange(ie.EMBED_DIM, dtype=np.float32)


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (120, 90), (3, 9, 27)).save(buf, format="PNG")
    return buf.getvalue()


class TestEmbeddingPersistence(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["RESKIOSK_ASSETS_DIR"] = self._tmp.name
        e = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(e)
        self.db = sessionmaker(bind=e)()
        self.stub = _StubEmbedder()

    def tearDown(self):
        self.db.close()
        os.environ.pop("RESKIOSK_ASSETS_DIR", None)
        self._tmp.cleanup()

    def test_generate_and_store(self):
        asset = ia.store_asset(self.db, _png(), "image/png")
        ok = ie.generate_and_store_embedding(self.db, asset, kb_version=3, embedder=self.stub)
        self.assertTrue(ok)
        self.db.refresh(asset)
        self.assertEqual(asset.embedding_model, ie.MODEL_VERSION)
        self.assertEqual(asset.embedding_kb_version, 3)
        vec = deserialize_embedding(asset.embedding)
        self.assertEqual(vec.shape[0], ie.EMBED_DIM)

    def test_readiness_gate_skips_non_ready(self):
        asset = ia.store_asset(self.db, _png(), "image/png")
        ia.set_status(self.db, asset, ia.STATUS_REJECTED, "x")
        self.assertFalse(ie.generate_and_store_embedding(self.db, asset, 1, embedder=self.stub))
        self.db.refresh(asset)
        self.assertIsNone(asset.embedding)

    def test_needs_embedding_invalidation_on_model_change(self):
        asset = ia.store_asset(self.db, _png(), "image/png")
        ie.generate_and_store_embedding(self.db, asset, 1, embedder=self.stub)
        self.assertFalse(ie.needs_embedding(asset))                 # current model
        self.assertTrue(ie.needs_embedding(asset, "different-model"))  # model changed -> stale

    def test_embed_ready_assets_batch_and_restamp(self):
        asset = ia.store_asset(self.db, _png(), "image/png")
        item = schema.KBItem(question="b", answer="(image)", modality="image",
                             image_asset_id=asset.id, enabled=1, created_at=0, last_updated=0)
        self.db.add(item)
        self.db.commit()

        n = ie.embed_ready_assets(self.db, kb_version=5, embedder=self.stub)
        self.assertEqual(n, 1)
        self.db.refresh(asset)
        self.assertEqual(asset.embedding_kb_version, 5)

        # second publish: nothing new to embed, but kb_version re-stamped
        n2 = ie.embed_ready_assets(self.db, kb_version=6, embedder=self.stub)
        self.assertEqual(n2, 0)
        self.db.refresh(asset)
        self.assertEqual(asset.embedding_kb_version, 6)


if __name__ == "__main__":
    unittest.main()

"""
hub/tests/test_image_embedder.py

Phase 9 / Slice 7C — image/text encoder wiring (S7C.1/2). The real CLIP model is
never loaded: SentenceTransformer is patched and RESKIOSK_CLIP_MODEL_PATH points
at a temp dir so the load path + encode wiring are exercised hermetically.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import numpy as np

from hub.retrieval import image_embedder as ie


class _FakeST:
    """Stand-in for SentenceTransformer: returns a deterministic vector."""
    def __init__(self, *a, **k):
        self.args = a
        self.kwargs = k

    def encode(self, x, convert_to_numpy=True):
        # text -> length-based vector; image -> fixed vector. Deterministic.
        if isinstance(x, str):
            return np.array([float(len(x))] + [0.0] * (ie.EMBED_DIM - 1), dtype=np.float32)
        return np.ones(ie.EMBED_DIM, dtype=np.float32)


class TestImageEmbedder(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["RESKIOSK_CLIP_MODEL_PATH"] = self._tmp.name
        ie.reset_image_embedder()

    def tearDown(self):
        os.environ.pop("RESKIOSK_CLIP_MODEL_PATH", None)
        ie.reset_image_embedder()

    def test_loads_offline_cpu_local_only(self):
        with patch("hub.retrieval.image_embedder.SentenceTransformer", _FakeST):
            emb = ie.load_image_embedder()
        self.assertEqual(emb.model.kwargs.get("device"), "cpu")
        self.assertTrue(emb.model.kwargs.get("local_files_only"))
        self.assertEqual(emb.model_name, ie.MODEL_NAME)

    def test_embed_text_dim(self):
        with patch("hub.retrieval.image_embedder.SentenceTransformer", _FakeST):
            v = ie.load_image_embedder().embed_text("where is the building")
        self.assertEqual(v.shape[0], ie.EMBED_DIM)

    def test_embed_image_dim_and_singleton(self):
        with patch("hub.retrieval.image_embedder.SentenceTransformer", _FakeST):
            e1 = ie.load_image_embedder()
            e2 = ie.load_image_embedder()
            v = e1.embed_image(MagicMock())  # PIL stand-in; FakeST ignores it
        self.assertEqual(v.shape[0], ie.EMBED_DIM)
        self.assertIs(e1, e2)  # process singleton

    def test_missing_model_path_raises(self):
        os.environ["RESKIOSK_CLIP_MODEL_PATH"] = os.path.join(self._tmp.name, "nope")
        ie.reset_image_embedder()
        with self.assertRaises(FileNotFoundError):
            ie.load_image_embedder()

    def test_cosine_sim(self):
        q = np.array([1.0, 0.0, 0.0])
        m = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 0.0]])
        sims = ie.cosine_sim(q, m)
        self.assertAlmostEqual(sims[0], 1.0, places=5)
        self.assertAlmostEqual(sims[1], 0.0, places=5)
        self.assertAlmostEqual(sims[2], 0.70710, places=4)


if __name__ == "__main__":
    unittest.main()

"""
hub/tests/test_image_assets.py

Phase 8 / Slice 7B — image asset service: storage, content hashing, dedup,
deterministic thumbnail + rendition, aspect preservation.
"""

import io
import os
import tempfile
import unittest

from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hub.db.session import Base
from hub.db import schema


def _png(w=400, h=300, color=(120, 60, 30)) -> bytes:
    img = Image.new("RGB", (w, h), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class ImageAssetTestBase(unittest.TestCase):
    def setUp(self):
        # Isolate the assets dir per test.
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["RESKIOSK_ASSETS_DIR"] = self._tmp.name
        # Reimport fresh so module-level config picks up the env (assets_dir reads env at call time).
        global ia
        from hub.services import image_assets as ia  # noqa
        self._ia = ia
        e = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(e)
        self.db = sessionmaker(bind=e)()

    def tearDown(self):
        self.db.close()
        os.environ.pop("RESKIOSK_ASSETS_DIR", None)
        self._tmp.cleanup()


class TestHashingAndStore(ImageAssetTestBase):
    def test_store_creates_ready_asset_with_refs(self):
        asset = self._ia.store_asset(self.db, _png(), "image/png")
        self.assertEqual(asset.status, self._ia.STATUS_READY)
        self.assertTrue(asset.content_hash)
        self.assertEqual(asset.width, 400)
        self.assertEqual(asset.height, 300)
        for ref in (asset.original_ref, asset.thumb_ref, asset.rendition_ref):
            self.assertTrue((self._ia.assets_dir() / ref).exists())

    def test_content_hash_deterministic(self):
        data = _png()
        self.assertEqual(self._ia.sha256_hex(data), self._ia.sha256_hex(data))

    def test_global_dedup_same_bytes(self):
        data = _png()
        a1 = self._ia.store_asset(self.db, data, "image/png")
        a2 = self._ia.store_asset(self.db, data, "image/png")
        self.assertEqual(a1.id, a2.id)  # same bytes -> same asset row
        self.assertEqual(self.db.query(schema.ImageAsset).count(), 1)

    def test_rejects_unsupported_mime(self):
        with self.assertRaises(self._ia.AssetError) as ctx:
            self._ia.store_asset(self.db, b"not-an-image", "application/pdf")
        self.assertEqual(ctx.exception.reason, self._ia.REASON_UNSUPPORTED_MIME)

    def test_rejects_too_large(self):
        orig = self._ia.MAX_BYTES
        try:
            self._ia.MAX_BYTES = 10
            with self.assertRaises(self._ia.AssetError) as ctx:
                self._ia.store_asset(self.db, _png(), "image/png")
            self.assertEqual(ctx.exception.reason, self._ia.REASON_TOO_LARGE)
        finally:
            self._ia.MAX_BYTES = orig

    def test_decode_failure(self):
        with self.assertRaises(self._ia.AssetError) as ctx:
            self._ia.store_asset(self.db, b"\x89PNG-garbage", "image/png")
        self.assertEqual(ctx.exception.reason, self._ia.REASON_DECODE_FAILED)


class TestDeterministicDerivatives(ImageAssetTestBase):
    def test_thumbnail_deterministic(self):
        data = _png()
        self.assertEqual(self._ia.generate_thumbnail(data), self._ia.generate_thumbnail(data))

    def test_rendition_deterministic(self):
        data = _png()
        self.assertEqual(self._ia.generate_rendition(data), self._ia.generate_rendition(data))

    def test_thumbnail_shrinks_and_preserves_aspect(self):
        data = _png(800, 400)
        out = self._ia.generate_thumbnail(data)
        im = Image.open(io.BytesIO(out))
        self.assertLessEqual(max(im.size), self._ia.THUMB_MAX)
        # 2:1 aspect preserved
        self.assertAlmostEqual(im.size[0] / im.size[1], 2.0, places=1)

    def test_no_upscale_small_image(self):
        data = _png(64, 48)
        im = Image.open(io.BytesIO(self._ia.generate_rendition(data)))
        self.assertEqual(im.size, (64, 48))  # rendition never enlarges

    def test_rendition_hash_stored(self):
        asset = self._ia.store_asset(self.db, _png(), "image/png")
        self.assertTrue(asset.rendition_hash)


class TestResidentFacingGate(ImageAssetTestBase):
    def test_only_ready_is_resident_facing(self):
        asset = self._ia.store_asset(self.db, _png(), "image/png")
        self.assertTrue(self._ia.is_resident_facing(asset))
        asset.status = self._ia.STATUS_REJECTED
        self.assertFalse(self._ia.is_resident_facing(asset))
        self.assertFalse(self._ia.is_resident_facing(None))

    def test_render_ref_shape(self):
        self.assertEqual(self._ia.render_ref(7, self._ia.VARIANT_THUMB), "/assets/7/thumb")


if __name__ == "__main__":
    unittest.main()

"""
hub/tests/test_image_asset_states.py

Phase 8 / Slice 7B — 4-state transitions, KB-version linkage (publish), and the
broken/missing-artifact guard.
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
from hub.services import image_assets as ia


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (200, 150), (5, 5, 5)).save(buf, format="PNG")
    return buf.getvalue()


class TestStatesAndLinkage(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["RESKIOSK_ASSETS_DIR"] = self._tmp.name
        e = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(e)
        self.db = sessionmaker(bind=e)()

    def tearDown(self):
        self.db.close()
        os.environ.pop("RESKIOSK_ASSETS_DIR", None)
        self._tmp.cleanup()

    def test_set_status_transitions(self):
        asset = ia.store_asset(self.db, _png(), "image/png")
        self.assertEqual(asset.status, ia.STATUS_READY)
        ia.set_status(self.db, asset, ia.STATUS_REJECTED, failure_reason="bad_content")
        self.assertEqual(asset.status, ia.STATUS_REJECTED)
        self.assertEqual(asset.failure_reason, "bad_content")
        self.assertFalse(ia.is_resident_facing(asset))

    def test_broken_artifact_guard(self):
        asset = ia.store_asset(self.db, _png(), "image/png")
        self.assertTrue(ia.asset_files_ok(asset))
        # delete a derivative -> guard fails
        (ia.assets_dir() / asset.thumb_ref).unlink()
        self.assertFalse(ia.asset_files_ok(asset))

    def test_link_assets_to_kb_version(self):
        asset = ia.store_asset(self.db, _png(), "image/png")
        item = schema.KBItem(question="building", answer="(image)", modality="image",
                             image_asset_id=asset.id, enabled=1, created_at=0, last_updated=0)
        self.db.add(item)
        self.db.commit()

        linked = ia.link_assets_to_kb_version(self.db, 5)
        self.assertEqual(linked, 1)
        self.db.refresh(asset)
        self.assertEqual(asset.kb_version, 5)

    def test_link_skips_unreferenced_or_not_ready(self):
        # ready but unreferenced -> not linked
        ia.store_asset(self.db, _png(), "image/png")
        self.assertEqual(ia.link_assets_to_kb_version(self.db, 9), 0)

    def test_link_skips_non_ready_even_if_referenced(self):
        asset = ia.store_asset(self.db, _png(), "image/png")
        ia.set_status(self.db, asset, ia.STATUS_FAILED, "x")
        item = schema.KBItem(question="b", answer="(image)", image_asset_id=asset.id,
                             enabled=1, created_at=0, last_updated=0)
        self.db.add(item)
        self.db.commit()
        self.assertEqual(ia.link_assets_to_kb_version(self.db, 3), 0)


if __name__ == "__main__":
    unittest.main()
